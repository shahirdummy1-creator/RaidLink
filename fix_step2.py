with open('App.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "payment_url = 'https://rzp.io/rzp/TZPCMrau'" in line:
        # Get the base URL from request
        lines[i] = (
            "                    base = request.host_url.rstrip('/')\n"
            "                    callback = f\"{base}/driver-signup/step2?username={username}\"\n"
            "                    payment_url = f'https://rzp.io/rzp/TZPCMrau?callback_url={callback}' if plan == 'yearly' else f'https://rzp.io/rzp/iZvG09vT?callback_url={callback}'\n"
        )
        break

with open('App.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Done")
