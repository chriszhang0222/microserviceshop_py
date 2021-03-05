from peewee import *
from datetime import datetime
from order_service.settings import settings


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


class ShoppingCart(BaseModel):
    user = IntegerField()
    goods = IntegerField()
    nums = IntegerField()
    checked = BooleanField(default=True)


class OrderInfo(BaseModel):
    ORDER_STATUS = (
        ("TRADE_SUCCESS", "Success"),
        ("TRADE_CLOSED", "Closed"),
        ("WAIT_FOR_PAY", "Created Order"),
        ("TRADE_FINISHED", "Trade Complete")
    )
    PAY_TYPE = (
        ("alipay", "ALIPAY")
    )
    user = IntegerField()
    order_sn = CharField(max_length=30, null=True, unique=True)
    pay_type = CharField(choices=PAY_TYPE, default="alipay", max_length=30)
    status = CharField(choices=ORDER_STATUS, default="paying", max_length=30)
    trade_no = CharField(max_length=100, unique=True, null=True)
    order_amount = FloatField(default=0.0)
    pay_time = DateTimeField(null=True)

    address = CharField(max_length=100, default="", verbose_name="收货地址")
    signer_name = CharField(max_length=20, default="", verbose_name="签收人")
    singer_mobile = CharField(max_length=11, verbose_name="联系电话")
    post = CharField(max_length=200, default="", verbose_name="留言")


class OrderGoods(BaseModel):

    order = IntegerField()
    goods = IntegerField()
    goods_name = CharField(max_length=20, default="")
    goods_image = CharField(max_length=200, default="")
    goods_price = DecimalField()
    nums = IntegerField(default=0)


class OrderHistory(BaseModel):
    order_id = IntegerField()
    order_sn = CharField(max_length=20, default="")
    user = IntegerField()
    addr = CharField(max_length=200, default="")


if __name__ == "__main__":
    settings.DB.create_tables([ShoppingCart, OrderGoods, OrderInfo])




