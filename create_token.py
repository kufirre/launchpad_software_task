def create_token():
    cred = {"client_id": input("Client_id: "), "client_secret": input("client_secret: "), "user_agent": input("user_agent: "), "username": input("username: "), "password": input("password: ")}
    return cred
