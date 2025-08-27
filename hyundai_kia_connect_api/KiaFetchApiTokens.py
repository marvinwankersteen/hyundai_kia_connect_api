#!/usr/bin/env python3

import requests
import re
import sys
import json

# Constants
client_id = "fdc85c00-0a2f-4c64-bcb4-2cfb1500730a"
user_agent = (
    "Mozilla/5.0 (Linux; Android 4.1.1; Galaxy Nexus Build/JRO03C) "
    "AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.166 Mobile Safari/535.19_CCS_APP_AOS"
)
auth_domain = "https://idpconnect-eu.kia.com"
redirect_url = "https://prd.eu-ccapi.kia.com:8080/api/v1/user/oauth2/redirect"
debug = False

# Initialize session with headers
session = requests.Session()
session.headers.update({
    "User-Agent": user_agent,
    "Accept-Language": "de-DE,de;q=0.9",
})



def _debug_response(response):
    if not debug:
        return True
    """Print debugging information for the given response object."""
    print(f"URL: {response.url}")
    print(f"Status Code: {response.status_code}")
    print("Headers:")
    print(" Request:")
    for key, value in response.request.headers.items():
        print(f"  {key}: {value}")
    print(" Response:")
    for key, value in response.headers.items():
        print(f"  {key}: {value}")
    print("\nCookies stored in session:", session.cookies.get_dict())
    if response.text:
        print("\nResponse Content (truncated):")
        print(response.text[:1000])  # Truncate to first 500 characters for readability
    print("\n\n\n" + "=" * 80)



def _get_connector_session_key():
    """Retrieve the connector_session_key from the redirect URL."""
    url = (
        f"{auth_domain}/auth/api/v2/user/oauth2/authorize"
        f"?response_type=code&client_id={client_id}"
        f"&redirect_uri={redirect_url}"
        "&lang=de&state=ccsp"
    )
    response = session.get(url)
    _debug_response(response)

    print(f"\n        Fetch the connector_session_key...", end="")
    try:
        key = re.search(r'connector_session_key%3D([0-9a-fA-F-]{36})', response.url).group(1)
        if response.status_code == 200:
            print(f"successful.")
            return key
    except Exception:
        print(f" [ERROR] Could not extract connector_session_key. client_id might be invalid.")
        print(f"  Response URL: {response.url}")
        sys.exit(1)



def _build_oauth_authorize_url(connector_session_key):
    """Build the OAuth authorization URL with the connector_session_key."""
    return (
        f"{auth_domain}/auth/api/v2/user/oauth2/authorize"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_url}"
        "&response_type=code&scope=&state=ccsp"
        f"&connector_client_id=hmgid1.0-{client_id}"
        "&ui_locales=&connector_scope="
        f"&connector_session_key={connector_session_key}"
    )



def _get_tokens(code):
    """Get the token with the code"""
    url = (
        f"{auth_domain}/auth/api/v2/user/oauth2/token"
    )
    
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_url,
        "client_id": client_id,
        "client_secret": "secret",
    }

    try:
        response = session.post(url, data=data)
        _debug_response(response)
        if response.status_code == 200:
            tokens = response.json()
            return tokens
        else:
            print(f"\n❌ Error getting tokens from der API!\n{response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Error getting tokens: {e}")
        return None




def main():
    if len(sys.argv) == 1:
        url = "https://idpconnect-eu.kia.com/auth/api/v2/user/oauth2/authorize?ui_locales=de&scope=openid+profile+email+phone&response_type=code&client_id=peukiaidm-online-sales&redirect_uri=https%3A%2F%2Fwww.kia.com%2Fapi%2Fbin%2Foneid%2Flogin&state=aHR0cHM6Ly93d3cua2lhLmNvbS9kZS8"

        print(f"Step 1: Open your Browser (best is Chrome), CTRL+SHIFT+I, CTRL-SHIFT+P, type 'network conditions', uncheck 'Use browser default' and set the following user-agent:\n")
        print(f"        {user_agent}\n")
        print(f"Step 2: Open this URL:\n")
        print(f"        {url}\n")
        print(f"Step 3: Solve the reCAPTCHA and login with your credentials. After successful login, you get redirected to Kia's homepage.")
        confirm = input("        Was the login successful? (y/n): ").strip().lower()

        if confirm != "y":
            print("Exiting script. Please try again after successful login.")
            sys.exit(1)

        connector_session_key = _get_connector_session_key()
        auth_url = _build_oauth_authorize_url(connector_session_key)

        print(f"\nStep 4: Open the following URL in the SAME browser tab where you're logged in:\n")
        print(f"        {auth_url}\n")
        redirect_url = input("Step 5: A blank page will open with the URL from step 4 which starts with 'https://prd.eu-ccapi.kia.com:8080/api/v1/user/oauth2/redirect?code=...'\n        Copy the full URL from the address bar and paste it here:\n> ")

        try:
            code = re.search(
                r'code=([0-9a-fA-F-]{36}\.[0-9a-fA-F-]{36}\.[0-9a-fA-F-]{36})',
                redirect_url
            ).group(1)
        except Exception:
            print("[ERROR] Could not extract authorization code from the URL. Please try again.")
            sys.exit(1)

        tokens = _get_tokens(code)
        if tokens is not None:
            refresh_token = tokens["refresh_token"]
            access_token = tokens["access_token"]
            print(f"\n✅ Your tokens are:\n\n- Refresh Token: {refresh_token}\n- Access Token: {access_token}")

if __name__ == "__main__":
    main()
