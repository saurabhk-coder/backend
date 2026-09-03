class EmailConfig:
    MAIL_USERNAME = ""
    MAIL_PASSWORD = ""
    MAIL_FROM = ""
    MAIL_PORT = 587
    MAIL_SERVER = "smtp-relay.sendinblue.com"
    MAIL_FROM_NAME = "aaralia"

    MAIL_TLS = False
    MAIL_SSL = False
    USE_CREDENTIALS = True

    URL = "https://dev-crm-api.aaralia.com/api/auth/api/v1/auth/verify_email?token="
    FORGET_URL = "https://qa-crm.aaraliapro.com/reset-password?token="
    APP_FORGET_URL = "/set-password?email="
    SAVE_URL = "https://dev-crm-api.aaralia.com/api/auth/api/v1/auth/save-password"