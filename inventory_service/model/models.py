from peewee import *
from datetime import datetime
from inventory_service.settings import settings
from playhouse.mysql_ext import JSONField


class BaseModel(Model):
    add_time = DateTimeField(default=datetime.now)
    is_deleted = BooleanField(default=False)
    update_time = DateTimeField(default=datetime.now)

    def save(self, *args, **kwargs):
        # 判断这是一个新添加的数据还是更新的数据
        if self._pk is not None:
            # 这是一个新数据
            self.update_time = datetime.now()
        return super().save(*args, **kwargs)

    @classmethod
    def delete(cls, permanently=False):  # permanently表示是否永久删除
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


class Inventory(BaseModel):
    goods = IntegerField(unique=True)
    stocks = IntegerField(default=0)
    version = IntegerField(default=0)


if __name__ == "__main__":
    settings.DB.create_tables([Inventory])