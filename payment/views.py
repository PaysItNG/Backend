from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated  
from django.db import transaction
from .utils import PayStackUtils
from .models import PaystackRecipient,DedicatedAccount
from main.models import Transaction, Wallet  # Assuming Wallet stores user balances
from django.conf import settings
import json  
import hmac  
import hashlib  
from .serializers import DedicatedAccountSerializer
from django.shortcuts import get_object_or_404  

#import os  
User = get_user_model()
PSTACK_PUBLIC_KEY=settings.PSTACK_PUB_KEY
PSTACK_SECRET_KEY=settings.PSTACK_SECRET_KEY
PayStack =PayStackUtils()
@method_decorator(csrf_exempt, name='dispatch')
class PaystackWebhook(APIView):
    """Webhook to handle Paystack payment events"""

    def post(self, request, *args, **kwargs):
        signature = request.headers.get('x-paystack-signature')  
        if not self._is_valid_signature(request.body, signature):  
            return Response({"error": "Invalid signature"}, status=status.HTTP_403_FORBIDDEN) 
        try:
            payload = json.loads(request.body)
            if payload.get("event") != "charge.success":
                return Response({"message": "Invalid event type"}, status=status.HTTP_400_BAD_REQUEST)

            data = payload.get("data", {})
            reference = data.get("reference")
            amount = int(data.get("amount", 0)) / 100  # Convert from kobo to Naira
            customer_email = data.get("customer", {}).get("email")
            sender_name = data.get("metadata", {}).get("sender_name", "Paystack") # Adjust based on how you gather sender info  

            if Transaction.objects.filter(reference_id=reference).exists():
                return Response({"message": "Transaction already verified"}, status=status.HTTP_200_OK)

            verification_response = PayStack.verify_transaction(reference)
            if not verification_response.get("status") or verification_response["data"].get("status") != "success":
                return Response({"message": "Transaction verification failed"}, status=status.HTTP_400_BAD_REQUEST)

            user = User.objects.filter(email=customer_email).only("id").first()
            if not user:
                return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

            # Use atomic transaction to prevent race conditions
            with transaction.atomic():
                wallet, _ = Wallet.objects.get_or_create(user=user)
                wallet.balance = wallet.balance + amount
                wallet.save(update_fields=["balance"])  # Efficient update

                Transaction.objects.create(
                    user=user,
                    to_from= data.get('sender_bank_account_number'),
                    sender_name =sender_name,
                    transaction_type="Deposit",
                    amount=amount,
                    status="completed",
                    payment_type="credit",
                    reference_id=reference,
                    description=data.get('narration')
                )

            return Response({"message": "User credited successfully"}, status=status.HTTP_200_OK)

        except json.JSONDecodeError:
            return Response({"error": "Invalid JSON data"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def _is_valid_signature(self, request_body, received_signature):  
        """Validate the Paystack request signature."""  
        calculated_signature = hmac.new(  
            PSTACK_SECRET_KEY.encode(),  
            request_body,  
            hashlib.sha512  
        ).hexdigest()  
        return hmac.compare_digest(calculated_signature, received_signature)  

class BankList(APIView):
    def get(self,request): 
        bank_response = PayStack.get_bank_list()  
        # Check if there was an error and handle accordingly  
        if isinstance(bank_response, tuple) and len(bank_response) == 2:  
            # Unpack error response  
            return Response(bank_response[0], status=bank_response[1])  
        return Response(bank_response, status=status.HTTP_200_OK) 
        


class BankTransfer(APIView): 
    """View to handle bank transfers using Paystack."""  
    permission_classes = [IsAuthenticated] 
    def post(self, request):
        user = request.user  
        amount = request.data.get('amount')  
        account_number = request.data.get('account_number')  
        bank_code = request.data.get('bank_code')  
        name = request.data.get('reciever_name')  
        wallet = get_object_or_404(Wallet,user)
        if wallet and wallet.balance >amount:
            if not all([amount,account_number,bank_code]):  
                return Response({'error': 'Amount, account number, and bank code are required.'}, status=status.HTTP_400_BAD_REQUEST)  
            # Check if recipient already exists  
            try:  
                recipient = PaystackRecipient.objects.get(account_number=account_number, bank_code=bank_code)  
            except PaystackRecipient.DoesNotExist:  
                # Create a new recipient if they do not exist  
                transfer_recipient = PayStack.create_transfer_recipient(name, account_number, bank_code)  
                if 'error' in transfer_recipient:  # Assuming the API returns an error key on failure  
                    return Response(transfer_recipient, status=status.HTTP_400_BAD_REQUEST)  
                # Save the recipient code in the database  
                recipient_code = transfer_recipient.get('data', {}).get('recipient_code')  
                bank_name = transfer_recipient.get('data', {}).get('bank_name')  
                recipient = PaystackRecipient.objects.create(
                    name=name,  
                    account_number=account_number,  
                    bank_code=bank_code,  
                    bank_name =bank_name,
                    recipient_code=recipient_code  
                )  
            # Now perform the transfer 
            transfer_response = PayStack.transfer(amount, recipient.recipient_code)  
            if 'error' in transfer_response:  # Assuming the API returns an error key on failure  
                return Response(transfer_response, status=status.HTTP_400_BAD_REQUEST)
            wallet.balance-=amount
            wallet.save()
              # Create a transaction instance for the successful transfer  
            Transaction.objects.create(  
                user=user,  
                to_from=recipient.account_number,  # Assuming this indicates where money is being transferred to  
                transaction_type='transfer',  
                amount=amount,  
                status='processing',  
                payment_type='debit',  # As it's a transfer (debiting the user's account)  
                description=f'Transfer to {name} ({recipient.account_number})',  
            )      
            return Response({'success': 'Transfer completed!', 'data': transfer_response}, status=status.HTTP_200_OK)  
        else:
            return Response({"error": "insufficent wallet"}, status=status.HTTP_400_BAD_REQUEST)
    
class DedicatedAccountList(APIView): #this API isfor testing via postman, users DVA will be created on signup 
    """View to retrieve dedicated bank accounts for the authenticated user."""  
    permission_classes = [IsAuthenticated]  # Ensure that the user is authenticated  
    def get(self, request):  
        # Get the currently authenticated user  
        user = request.user  
        try:  
            dedicated_accounts = DedicatedAccount.objects.filter(user=user)  
            if not dedicated_accounts.exists():  
                return Response({'message': 'No dedicated bank accounts found for this user.'}, status=status.HTTP_404_NOT_FOUND)  
            serializer = DedicatedAccountSerializer(dedicated_accounts, many=True)  
            return Response(serializer.data, status=status.HTTP_200_OK)  
        except Exception as e:  
            return Response({'error': 'An error occurred while retrieving dedicated accounts.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)  
        
        
class CreateDBAAPI(APIView):# used for just Testing
    permission_classes=[IsAuthenticated]
    #authentication_classes=[is]
    def post(self,request):
        data = request.data.copy()
        if not data:
            return Response({"error":"No valid data"}, status=status.HTTP_400_BAD_REQUEST)  

        email =data.get("email")
        first_name =data.get("first_name")
        last_name = data.get("last_name")
        phone_number = data.get("phone_number")
        if all([email,first_name,last_name,phone_number]):
            paystack_data =PayStack.create_paystack_customer(email,first_name,last_name,phone_number)
            if paystack_data['status']:
                created_account = PayStack.create_virtual_account(customer_code=paystack_data['data']['customer_code'])
                #print(created_account)
                if created_account['status']:
                    DedicatedAccount.objects.create(user=request.user,
                                     bank_name= created_account['data']['bank'],
                                     account_number=created_account['data']['account_number'],
                                     account_name =created_account['data']['account_name']
                                     )
                return Response(created_account, status=status.HTTP_201_CREATED)  
            else:
                return Response({paystack_data}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error":"missing data fields"}, status=status.HTTP_400_BAD_REQUEST)  
  

         