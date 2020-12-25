from peewee import *
from datetime import datetime
from goods_service.settings import settings
from playhouse.mysql_ext import JSONField


class BaseModel(Model):
    add_time = DateTimeField(default=datetime.now())
    is_deleted = BooleanField(default=False)
    update_time = DateTimeField(default=datetime.now())

    class Meta:
        database = settings.DB

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
        return super().select(*fields).where(cls.is_deleted==False)


class Category(BaseModel):
    name = CharField(max_length=20, verbose_name="Name")
    parent_category = ForeignKeyField("self", verbose_name="Parent category", null=True) #一级类别可以没有父类别
    level = IntegerField(default=1, verbose_name="Category")
    is_tab = BooleanField(default=False)


class Brands(BaseModel):
    name = CharField(max_length=50, verbose_name="Name", index=True, unique=True)
    logo = CharField(max_length=200, null=True, verbose_name="Logo", default="")


class Goods(BaseModel):
    category = ForeignKeyField(Category, on_delete='CASCADE')
    brand = ForeignKeyField(Brands, on_delete='CASCADE')
    on_sale = BooleanField(default=True)
    goods_sn = CharField(max_length=50, default="", verbose_name="Goods Number")
    name = CharField(max_length=100)
    click_num = IntegerField(default=0)
    sold_num = IntegerField(default=0)
    fav_num = IntegerField(default=0)
    market_price = FloatField(default=0)
    shop_price = FloatField(default=0)
    goods_brief = CharField(max_length=200)
    ship_free = BooleanField(default=True)
    images = JSONField()
    desc_images = JSONField()
    goods_front_image = CharField(max_length=200)
    is_new = BooleanField(default=False)
    is_hot = BooleanField(default=False)


class GoodsCategoryBrand(BaseModel):
    #品牌分类
    id = AutoField(primary_key=True, verbose_name="id")
    category = ForeignKeyField(Category, verbose_name="")
    brand = ForeignKeyField(Brands, verbose_name="")

    class Meta:
        indexes = (
            (("category", "brand"), True),
        )


class Banner(BaseModel):
    """
    轮播的商品
    """
    image = CharField(max_length=200, default="", verbose_name="图片url")
    url = CharField(max_length=200, default="", verbose_name="访问url")
    index = IntegerField(default=0, verbose_name="Order")


if __name__ == "__main__":
    # settings.DB.create_tables([Category,Goods, Brands, GoodsCategoryBrand, Banner])
    pass