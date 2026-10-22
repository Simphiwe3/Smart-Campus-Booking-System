from abc import ABC, abstractmethod


class User(ABC):
    def __init__(self, user_id, full_name, email, role, campus_id=None):
        self.__user_id = user_id
        self.__full_name = full_name
        self.__email = email
        self.__role = role
        self.__campus_id = campus_id

    @property
    def user_id(self):
        return self.__user_id

    @property
    def full_name(self):
        return self.__full_name

    @property
    def email(self):
        return self.__email

    @property
    def role(self):
        return self.__role

    @property
    def campus_id(self):
        return self.__campus_id

    @abstractmethod
    def allowed_actions(self):
        pass


class Lecturer(User):
    def allowed_actions(self):
        return {
            "book_resource",
            "view_own_bookings",
            "cancel_own_booking"
        }


class CampusAdministrator(User):
    def allowed_actions(self):
        return {
            "manage_resources",
            "view_campus_bookings",
            "view_campus_reports"
        }


class SystemOperator(User):
    def allowed_actions(self):
        return {
            "view_all_bookings",
            "view_all_resources",
            "compare_campuses"
        }


def make_user(row):
    role_classes = {
        "Lecturer": Lecturer,
        "Campus Administrator": CampusAdministrator,
        "System Operator": SystemOperator
    }

    role = row["role"]

    if role not in role_classes:
        raise ValueError("Unknown user role.")

    return role_classes[role](
        row["user_id"],
        row["full_name"],
        row["email"],
        row["role"],
        row["campus_id"]
    )