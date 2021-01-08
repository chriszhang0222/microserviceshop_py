from peewee import *
from datetime import datetime
from userop_service.settings import settings


class BaseModel(Model):
    add_time = DateTimeField(default=datetime.now())
    is_deleted = BooleanField(default=False)
    update_time = DateTimeField(default=datetime.now())

    def save(self, *args, **kwargs):
        if self._pk is not None:
            self.update_time = datetime.now()
        return super().save(*args, **kwargs)

    @classmethod
    def delete(cls, permanently=False):
        if permanently:
            return super().delete()
        else:
            return super().update(is_deleted=True)

    def delete_instance(self, permanently=False, recursive=False, delete_nullable=False):
        if permanently:
            return self.delete(permanently).where(self._pk_expr()).execute()
        else:
            self.is_deleted = True
            self.save()

    @classmethod
    def select(cls, *fields):
        return super().select(*fields).where(cls.is_deleted == False)

    class Meta:
        database = settings.DB


class LeavingMessages(BaseModel):
    MESSAGE_CHOICES = (
        (1, "留言"),
        (2, "投诉"),
        (3, "询问"),
        (4, "售后"),
        (5, "求购")
    )
    user = IntegerField()
    message_type = IntegerField(default=1, choices=MESSAGE_CHOICES)
    subject = CharField(max_length=100, default="")
    message = TextField(default="")
    file = CharField(max_length=100, null=True)


class Address(BaseModel):
    user = IntegerField()
    province = CharField(max_length=100, default="", null=True)
    city = CharField(max_length=100, default="", null=True)
    district = CharField(max_length=100, default="")
    address = CharField(max_length=100, default="", null=False)
    country = CharField(max_length=20, default="CA", null=False)
    signer_name = CharField(max_length=100, default="", verbose_name="签收人")
    signer_mobile = CharField(max_length=11, default="", verbose_name="电话")


class UserFav(BaseModel):
    user = IntegerField()
    goods = IntegerField()

    class Meta:
        primary_key = CompositeKey('user', 'goods')

if __name__ == "__main__":
    settings.DB.create_tables([LeavingMessages, Address, UserFav])
