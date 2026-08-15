import http.server
import socketserver

PORT = 8085
socketserver.TCPServer.allow_reuse_address = True

class LegacySOAPHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.send_header("Content-type", "application/xml")
        self.end_headers()
        
        # The massive, complex enterprise XML payload
        xml_response = """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:cus="http://legacybank.com/customers">
   <soapenv:Header>
      <cus:AuthToken>DEMO_TOKEN_REDACTED</cus:AuthToken>
   </soapenv:Header>
   <soapenv:Body>
      <cus:GetCustomerDataResponse>
         <cus:CustomerProfile>
            <cus:InternalID>991029384</cus:InternalID>
            <cus:FullName>Monish K C</cus:FullName>
            <cus:RiskTier>LOW</cus:RiskTier>
         </cus:CustomerProfile>
         <cus:Accounts>
            <cus:Deposit>
               <cus:Checking>1542.50</cus:Checking>
               <cus:Savings>10500.00</cus:Savings>
               <cus:Currency>INR</cus:Currency>
            </cus:Deposit>
            <cus:Mortgage>
               <cus:LoanID>ML-55412</cus:LoanID>
               <cus:PrincipalRemaining>4500000.00</cus:PrincipalRemaining>
               <cus:InterestRate>7.5</cus:InterestRate>
               <cus:NextPaymentDue>2026-09-01</cus:NextPaymentDue>
            </cus:Mortgage>
         </cus:Accounts>
         <cus:RecentTransactions>
            <cus:Tx>
               <cus:Date>2026-08-14</cus:Date>
               <cus:Merchant>AWS Cloud Services</cus:Merchant>
               <cus:Amount>-450.00</cus:Amount>
            </cus:Tx>
            <cus:Tx>
               <cus:Date>2026-08-12</cus:Date>
               <cus:Merchant>Dodo Payments Inc</cus:Merchant>
               <cus:Amount>12500.00</cus:Amount>
            </cus:Tx>
         </cus:RecentTransactions>
      </cus:GetCustomerDataResponse>
   </soapenv:Body>
</soapenv:Envelope>"""
        self.wfile.write(xml_response.encode('utf-8'))

with socketserver.TCPServer(("", PORT), LegacySOAPHandler) as httpd:
    print(f"🏦 HUGE Legacy Bank SOAP Server running on port {PORT}...")
    httpd.serve_forever()
