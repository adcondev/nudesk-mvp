from reportlab.pdfgen import canvas

def create_pdf(path):
    c = canvas.Canvas(path)
    c.drawString(100, 750, "Bank Statement")
    c.drawString(100, 730, "Account Holder: John Doe")
    c.drawString(100, 710, "Account Number: 123456789")
    c.drawString(100, 690, "Statement Date: 2023-10-01")
    c.drawString(100, 670, "Total Deposits: $5000.00")
    c.drawString(100, 650, "Total Withdrawals: $2000.00")
    c.drawString(100, 630, "Ending Balance: $3000.00")
    c.save()

create_pdf("test_data/bank_statement.pdf")
