from io import BytesIO
from datetime import datetime
from django.core.exceptions import ValidationError
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from main.models import Transaction  # Adjust the import based on your project structure

def generate_statement_pdf(user, start_date, end_date):
    """
    Generates a PDF statement of account for a user within a specified date range.

    Args:
        user: The user for whom the statement is generated.
        start_date (str): The start date in 'YYYY-MM-DD' format.
        end_date (str): The end date in 'YYYY-MM-DD' format.

    Returns:
        BytesIO: A BytesIO object containing the PDF content.

    Raises:
        ValueError: If the date format is invalid or no transactions are found.
    """
    # Validate input dates
    if not start_date or not end_date:
        raise ValueError("Start date and end date are required")

    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError:
        raise ValueError("Invalid date format. Use YYYY-MM-DD")

    # Fetch transactions within the date range
    transactions = Transaction.objects.filter(
        user=user, created_at__range=[start_date, end_date]
    ).order_by('created_at')

    if not transactions.exists():
        raise ValueError("No transactions found within the selected date range")

    # Calculate opening balance (adjust this based on your balance logic)
    opening_balance = 0  # Replace with actual logic to calculate opening balance
    closing_balance = opening_balance

    # Prepare data for the PDF table
    data = [["Date", "Type", "Amount", "To / From", "Description", "Balance"]]

    for tx in transactions:
        if tx.payment_type in ['credit', 'payment']:
            closing_balance += tx.amount
        else:
            closing_balance -= tx.amount

        data.append([
            tx.created_at.strftime('%d/%m/%Y %H:%M:%S'),
            tx.transaction_type.capitalize(),
            f"₦{tx.amount:,.2f}",
            tx.to_from,
            tx.description,
            f"₦{closing_balance:,.2f}"
        ])

    # Generate the PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold')
    ]))
    doc.build([table])
    buffer.seek(0)
    return buffer