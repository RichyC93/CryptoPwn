from config import *
from coinbase.wallet.client import Client as CB_Client
from kucoin.client import Client as KC_Client
import base64, json, hashlib, hmac, random, re, requests, time, urllib, urllib3
urllib3.disable_warnings()

def Cryptopia_API_Query(method, req = None):
    public_set = set([
        "GetCurrencies", "GetTradePairs", "GetMarkets",
        "GetMarket", "GetMarketHistory", "GetMarketOrders"
    ])
    private_set = set([
        "GetBalance", "GetDepositAddress", "GetOpenOrders", "GetTradeHistory",
        "GetTransactions", "SubmitTrade", "CancelTrade", "SubmitTip", "SubmitWithdraw"
    ])
    url = "https://www.cryptopia.co.nz/api/" + method
    if not req: req = {}
    time.sleep(1)
    if method in public_set:
        if req:
            for param in req:
                url += '/' + str(param)
        r = requests.get(url, verify = False)
    elif method in private_set:
        nonce = str(int(time.time())); post_data = json.dumps(req); m = hashlib.md5(); m.update(post_data)
        requestContentBase64String = base64.b64encode(m.digest())
        signature = NZ_API_KEY + "POST" + urllib.quote_plus(url).lower() + nonce + requestContentBase64String
        hmacsignature = base64.b64encode(hmac.new(base64.b64decode(NZ_API_SECRET), signature, hashlib.sha256).digest())
        header_value = "amx " + NZ_API_KEY + ":" + hmacsignature + ":" + nonce
        headers = {"Authorization": header_value, "Content-Type": "application/json; charset = UTF-8"}
        r = requests.post(url, data = post_data, headers = headers)
    response = r.text
    return response

def CoinBaseBalance():
    print "Connecting To CoinBase..."
    client = CB_Client(CB_API_KEY, CB_API_SECRET, api_version = "2017-05-19")
    accounts = client.get_accounts(); wallets = {}
    for account in accounts.data:
        address_data = client.get_addresses(account.id).data
        x = int(random.random() * len(address_data)) #; x = 0
        wallet_address = address_data[x].address
        print "\tRetrieving %s Wallet Data" % account.currency.name
        wallets.update({
            account.balance.currency: {
                "AccountId": account.id, "Address": wallet_address, "Available": account.balance.amount,
                "Name": account.currency.name, "NativeBalance": account.native_balance.amount,
                "NativeCurrency": account.native_balance.currency, "Symbol": account.balance.currency,
                "TotalAmount": account.balance.amount
            }
        })
    wallets.update({"ExchangeName": "CoinBase.com"})
    print
    return wallets

def CryptopiaBalance():
    print "Connecting To Cryptopia..."
    CryptopiaCurrencies = json.loads(Cryptopia_API_Query("GetCurrencies"))["Data"]
    print "\tGetting Cryptopia Currencies..."
    SymbolData = {Currency["Symbol"]: {"Name": Currency["Name"]} for Currency in CryptopiaCurrencies}
    CryptopiaMarkets = json.loads(Cryptopia_API_Query("GetMarkets"))["Data"]
    for Market in CryptopiaMarkets:
        Label = Market["Label"].split("/")
        if Label[1] == "USDT": SymbolData[Label[0]].update({"ExchangeRate": Market["AskPrice"]})
    print "\tGetting Cryptopia Balances..."
    CryptopiaData = json.loads(Cryptopia_API_Query("GetBalance"))
    DefaultCoins = ["BTC", "DOGE", "LTC", "NZDT", "USDT"]
    wallets = {}
    for Wallet in CryptopiaData["Data"]:
        if float(Wallet["Total"]) or Wallet["Symbol"] in DefaultCoins:
            print "\t\tRetrieving %s Wallet Data" % SymbolData[Wallet["Symbol"]]["Name"]
            DepAddr = json.loads(Cryptopia_API_Query("GetDepositAddress", {"Currency": Wallet["Symbol"]}))
            if DepAddr["Data"]["BaseAddress"]: wallet_address = DepAddr["Data"]["BaseAddress"]
            else: wallet_address = DepAddr["Data"]["Address"]
            ExchangeRate = SymbolData[Wallet["Symbol"]]["ExchangeRate"] if Wallet["Symbol"] != "USDT" else "1.0"
            NativeBalance = str(float(Wallet["Available"]) * float(ExchangeRate)) if float(ExchangeRate) else False
            wallets.update({
                Wallet["Symbol"]: {
                    "Address": wallet_address, "Available": Wallet["Available"],
                    "Name": SymbolData[Wallet["Symbol"]]["Name"], "NativeBalance": NativeBalance,
                    "NativeCurrency": "USDT", "OnHold": Wallet["HeldForTrades"],
                    "PendingWithdraw": Wallet["PendingWithdraw"], "Symbol": Wallet["Symbol"],
                    "TotalAmount": Wallet["Total"]
                }
            })
    wallets.update({"ExchangeName": "Cryptopia.co.nz"})
    print
    return wallets

def KuCoinBalance():
    print "Connecting To KuCoin..."
    time.sleep(1)
    client = KC_Client(KC_API_KEY, KC_API_SECRET)
    DefaultCoins = ["BTC", "ETH", "KCS", "NEO", "USDT"]
    wallets = {}
    for Wallet in client.get_all_balances():
        # if float(Balance["Total"]):
        if float(Wallet["balance"]) or Wallet["coinType"] in DefaultCoins:
            print "\tRetrieving %s Wallet Data" % Wallet["coinType"]
            wallets.update({
                Wallet["coinType"]: {
                    "Address": "0", "Available": Wallet["balanceStr"],
                    "Symbol": Wallet["coinType"], "Name": Wallet["coinType"],
                    "NativeBalance": "0.0", "NativeCurrency": "USDT",
                    "OnHold": Wallet["freezeBalanceStr"], "TotalAmount": Wallet["balanceStr"]
                }
            })
    wallets.update({"ExchangeName": "KuCoin.com"})
    print
    return wallets

def BuyCrypto(account_id, amount, currency, commit = False):
    client = CB_Client(CB_API_KEY, CB_API_SECRET, api_version = "2017-05-19")
    tx = client.buy(account_id, total = amount, currency = currency, commit = commit)
    split_time = time.ctime().split()
    time_code = int(split_time[2]) + int(split_time[3].split(":")[0]) + int(split_time[4]) + 526
    confirm = raw_input("Enter Time Code: ")
    if confirm == str(time_code):
        tx.commit()
        print "Buy Confirmed"
    else: print "Buy NOT Confirmed"

def Send2Address(exchange, wallet, amount, address):
    print "SENDING %s %s FROM %s TO %s" % (amount, wallet["Symbol"], exchange, address)
    if exchange.upper() == "CB" or exchange.upper() == "COINBASE":
        print "Account ID:", wallet["AccountId"]; print "Address:", address
        print "Amount:", amount; print "Currency:", wallet["Symbol"]; print "idem:", time.time()
        client = CB_Client(CB_API_KEY, CB_API_SECRET, api_version = "2017-05-19")
        exchange_rates = client.get_exchange_rates()
        if wallet["Symbol"] == "BCH": fee = 0.0043 * float(exchange_rates["rates"]["BCH"])
        if wallet["Symbol"] == "BTC": fee = 5.2975 * float(exchange_rates["rates"]["BTC"])
        if wallet["Symbol"] == "ETH": fee = 1.05 * float(exchange_rates["rates"]["ETH"])
        if wallet["Symbol"] == "LTC": fee = 0.042 * float(exchange_rates["rates"]["LTC"])
        print str(float(amount) - fee)
        tx = client.send_money(wallet["AccountId"], amount = str(float(amount) - fee), currency =  wallet["Symbol"], to = address, type = "send")
        print tx
    if exchange.upper() == "NZ" or exchange.upper() == "CRYPTOPIA":
        tx = json.loads(Cryptopia_API_Query("SubmitWithdraw", {"Address": address, "Amount": amount,"Currency": wallet["Symbol"]}))
        print tx
    if exchange.upper() == "KC" or exchange.upper() == "KUCOIN":
        client = KC_Client(KC_API_KEY, KC_API_SECRET)
        client.create_withdrawal(wallet["Symbol"], amount, address)

def TxtFriendly(Wallets):
    txt = ""
    if Wallets:
        txt += "%s %s %s\n\n" % ("-" * 18, Wallets["ExchangeName"], "-" * 18)
        for Symbol in list(set(Wallets.keys()) - set(["ExchangeName"])):
            txt += "------- %s - %s -------\n" % (Wallets[Symbol]["Name"], Symbol)
            txt += "%s: %s\n" % ("Address", Wallets[Symbol]["Address"])
            txt += "%s: %s %s\n" % ("Available", Wallets[Symbol]["Available"], Symbol)
            txt += "%s: $%s %s\n" % ("Native Balance", Wallets[Symbol]["NativeBalance"], Wallets[Symbol]["NativeCurrency"])
            txt += "%s: %s %s\n" % ("Total Amount", Wallets[Symbol]["TotalAmount"], Symbol)
            OmitKeys = set(["Address", "Available", "Name", "NativeBalance", "NativeCurrency", "Symbol", "TotalAmount"])
            WalletKeys = set(Wallets[Symbol].keys())
            for key in sorted(WalletKeys - OmitKeys):
                txt += "%s: %s\n" % (key, Wallets[Symbol][key])
            txt += "\n"
    return txt

reply = raw_input("Enter SMS Message: ")
parseReply = reply.split(); txt = ""
exchanges = ["CB", "COINBASE", "KC", "KUCOIN", "NZ", "CRYPTOPIA"]
if len(parseReply) > 2 and " ".join(parseReply[:2]).upper() == "GET BALANCE":
    for symbol in set(parseReply[2:]):
        if symbol.upper() == "CB" or symbol.upper() == "COINBASE": txt += TxtFriendly(CoinBaseBalance())
        if symbol.upper() == "NZ" or symbol.upper() == "CRYPTOPIA": txt += TxtFriendly(CryptopiaBalance())
        if symbol.upper() == "KC" or symbol.upper() == "KUCOIN": txt += TxtFriendly(KuCoinBalance())
elif len(parseReply) == 2 and " ".join(parseReply[:2]).upper() == "GET BALANCES":
    txt += TxtFriendly(CoinBaseBalance()); txt += TxtFriendly(CryptopiaBalance()); txt += TxtFriendly(KuCoinBalance())
elif len(parseReply) == 5 and parseReply[0].upper() == "SEND" and parseReply[2].upper() in exchanges:
    if parseReply[2].upper() == "CB" or parseReply[2].upper() == "COINBASE": wallets = CoinBaseBalance()
    if parseReply[2].upper() == "NZ" or parseReply[2].upper() == "CRYPTOPIA": wallets = CryptopiaBalance()
    if parseReply[2].upper() == "KC" or parseReply[2].upper() == "KUCOIN": wallets = KuCoinBalance()
    if parseReply[3].upper() in wallets.keys():
        wallet = wallets[parseReply[3].upper()]
        all_amount = wallets[parseReply[3].upper()]["Available"]
    else:
        print "%s is not a coin" % parseReply[3]; quit()
    try: amount = float(parseReply[1])
    except ValueError:
        amount = 0.0
        if parseReply[1].upper() == "ALL": amount = all_amount
    if not amount: print "Invalid Amount"; quit()
    if float(amount) > float(all_amount):
        print "Amount is more than Available amount..."; quit()
    Send2Address(parseReply[2].upper(), wallet, amount, parseReply[4])
elif len(parseReply) == 4 and parseReply[0].upper() == "BUY":
    try: amount = float(parseReply[1])
    except ValueError: print "Invalid Amount..."; quit()
    wallets = CoinBaseBalance()
    if parseReply[2].upper() in wallets.keys() and parseReply[3].upper() in wallets.keys():
        BuyCrypto(wallets[parseReply[3].upper()]["AccountId"], amount, parseReply[2].upper())

else: print "To Be Continued..."
print txt
