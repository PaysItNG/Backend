from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model
import json
from django.db import transaction
from .utils import PayStackUtils
from .models import PaystackRecipient
from main.models import Transaction, Wallet  # Assuming Wallet stores user balances

User = get_user_model()


@method_decorator(csrf_exempt, name='dispatch')
class PaystackWebhook(APIView):
    """Webhook to handle Paystack payment events"""

    def post(self, request, *args, **kwargs):
        try:
            payload = json.loads(request.body)
            if payload.get("event") != "charge.success":
                return Response({"message": "Invalid event type"}, status=status.HTTP_400_BAD_REQUEST)

            data = payload.get("data", {})
            reference = data.get("reference")
            amount = int(data.get("amount", 0)) / 100  # Convert from kobo to Naira
            customer_email = data.get("customer", {}).get("email")

            verification_response = PayStackUtils.verify_transaction(reference)
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
                    to_from="Paystack",
                    transaction_type="deposit",
                    amount=amount,
                    status="completed",
                    payment_type="credit",
                    description="Deposit to wallet",
                    reference_id=reference,
                )

            return Response({"message": "User credited successfully"}, status=status.HTTP_200_OK)

        except json.JSONDecodeError:
            return Response({"error": "Invalid JSON data"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TransferMoneyView(APIView):
    """Create a recipient if needed and transfer money"""

    def post(self, request):
        user = request.user
        account_name = request.data.get("account_name")
        account_number = request.data.get("account_number")
        bank_code = request.data.get("bank_code")
        amount = request.data.get("amount")
        reason = request.data.get("reason", "Payment")

        if not all([account_name, account_number, bank_code, amount]):
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Get or create recipient
            recipient, created = PaystackRecipient.objects.get_or_create(
                user=user,
                account_number=account_number,
                defaults={"bank_code": bank_code}
            )

            if created:
                recipient_response = PayStackUtils.create_transfer_recipient(account_name, account_number, bank_code)
                if not recipient_response.get("status"):
                    return Response({"error": recipient_response.get("message")}, status=status.HTTP_400_BAD_REQUEST)

                recipient.recipient_code = recipient_response["data"]["recipient_code"]
                recipient.save(update_fields=["recipient_code"])  # Only update recipient_code field
            # Transfer money
            transfer_response = PayStackUtils.transfer(amount, recipient.recipient_code, reason)
            if not transfer_response.get("status"):
                return Response({"error": transfer_response.get("message")}, status=status.HTTP_400_BAD_REQUEST)

            return Response(
                {"message": "Transfer successful", "data": transfer_response["data"]},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)