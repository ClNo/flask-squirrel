# Contains a deep copy of all important application specifications; used for instance for getting the primary ID
class ClientAppConfig:
    db_spec = None
    customview_spec = None
    translation_spec = None
    api_path = None
    default_admin_user = None
    session_dir = None

    upload_dir = None
    archive_dir = None


client_config = ClientAppConfig()
