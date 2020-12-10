from peewee import *
from user_service.settings import setting


class BaseModel(Model):
    class Meta:
        database = setting.DB


GENDER_CHOICES = (
    ("female", "Female"),
    ("male", "Male"),
    ("unknown", "Unknown")
)

ROLE_CHOICES = (
    (1, "User"),
    (2, "Admin")
)


class User(BaseModel):
    mobile = CharField(max_length=11, index=True, unique=True, verbose_name="Phone Number")
    password = CharField(max_length=200, verbose_name="Password")
    nick_name = CharField(max_length=20, verbose_name="Username", null=True)
    head_url = CharField(max_length=200, null=True, verbose_name="Avatar")
    birthday = DateField(null=True)
    address = CharField(max_length=200, null=True)
    gender = CharField(max_length=6, null=True, choices=GENDER_CHOICES)
    role = IntegerField(default=1, choices=ROLE_CHOICES)


if __name__ == "__main__":
    setting.DB.create_tables([User])
