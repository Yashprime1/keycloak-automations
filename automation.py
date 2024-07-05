import time
import requests
import argparse
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(format='[%(asctime)s] [%(levelname)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument("--client_id", help="Client Id", required=True)
parser.add_argument("--client_secret_key", help="Client secret key", required=True)
args = parser.parse_args()

logging.info(f"Arguments parsed")

client_id = args.client_id
client_secret_key = args.client_secret_key


access_token = None
access_token_expiry = 0


def get_access_token():
    global access_token, access_token_expiry
    try:
        url = "https://id.clevertap.net/auth/realms/master/protocol/openid-connect/token"
        payload = f"grant_type=client_credentials&client_id={client_id}&client_secret={client_secret_key}"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        response.raise_for_status()
        res = response.json()
        access_token = res["access_token"]
        expires_in = res["expires_in"]
        access_token_expiry = time.time() + expires_in
        return access_token
    except requests.exceptions.RequestException as e:
        logging.error(f"Error getting access token: {e}")
        return None


def get_valid_access_token():
    if time.time() >= access_token_expiry:
        return get_access_token()
    return access_token


def get_users():
    try:
        token = get_valid_access_token()
        if token is None:
            return []
        url = f"https://id.clevertap.net/auth/admin/realms/CleverTap/users?max=2000&enabled=true"
        headers = {
            'Authorization': f"Bearer {token}"
        }
        response = requests.request("GET", url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error getting users: {e}")
        return []


def get_user_sessions(user_id):
    try:
        token = get_valid_access_token()
        if token is None:
            return []
        url = f"https://id.clevertap.net/auth/admin/realms/CleverTap/users/{user_id}/sessions"
        headers = {
            'Authorization': f"Bearer {token}"
        }
        response = requests.request("GET", url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error getting user sessions for user {user_id}: {e}")
        return []


def delete_inactive_user_sessions():
    try:
        users = get_users()
        logging.info("Number of users ", len(users))

        for user in users:
            user_id = user["id"]
            logging.info("Deleting User session for user: ", user["username"])
            user_sessions = get_user_sessions(user_id)
            if user_sessions:
                for session in user_sessions:
                    if session["clients"] == {}:
                        session_id = session["id"]
                        token = get_valid_access_token()
                        if token is None:
                            continue
                        url = f"https://id.clevertap.net/auth/admin/realms/CleverTap/sessions/{session_id}"
                        headers = {
                            "Authorization": f"Bearer {token}"
                        }
                        try:
                            response = requests.request("DELETE", url=url, headers=headers)
                            response.raise_for_status()
                        except requests.exceptions.RequestException as e:
                            logging.error(f"Error deleting session {session_id}: {e}")
    except Exception as e:
        logging.error(f"Error in delete_inactive_user_sessions: {e}")


def main():
    delete_inactive_user_sessions()


if __name__ == '__main__':
    main()