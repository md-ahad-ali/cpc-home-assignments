class ImportManager:
    def __init__(self, user_id):
        self.__user_id = user_id
        self.__import_status = "PENDING"
        self.__total_imported = 0

    def get_user_id(self):
        return self.__user_id

    def set_user_id(self, user_id):
        self.__user_id = user_id

    def get_import_status(self):
        return self.__import_status

    def set_import_status(self, import_status):
        self.__import_status = import_status

    def get_total_imported(self):
        return self.__total_imported

    def bulk_insert(self, logs):
        try:
            self.__total_imported = len(logs)
            self.__import_status = "SUCCESS"
            return True
        except Exception:
            self.rollback_import()
            return False

    def rollback_import(self):
        self.__import_status = "ROLLED_BACK"
        self.__total_imported = 0