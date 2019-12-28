import os
import random
import datetime
from datetime import datetime, timedelta
from flask import Flask, request, session, flash, render_template, redirect, url_for
from flask_user import current_user, login_required, roles_required, UserManager, UserMixin, user_logged_in, user_logged_out
from flask_babelex import Babel
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, MetaData, func, desc
from flask_login import LoginManager, login_user, logout_user
from werkzeug.utils import secure_filename


class ConfigClass(object):
    SECRET_KEY = 'Betul Cihan Mucahit | Python Flask Alisveris Sitesi Projesi | Betik Diller'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///alisveris.sqlite'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = 'smtp.yandex.com'
    MAIL_PORT = 587
    MAIL_USE_SSL = False
    MAIL_USE_TLS = True
    MAIL_USERNAME = '@yandex.com'
    MAIL_PASSWORD = ''
    MAIL_DEFAULT_SENDER = '"Flask Alışveriş" <webibo@yandex.com>'

    USER_APP_NAME = "Flask Alışveriş"
    USER_ENABLE_EMAIL = True
    USER_ENABLE_USERNAME = False
    USER_EMAIL_SENDER_NAME = USER_APP_NAME
    USER_EMAIL_SENDER_EMAIL = "webibo@yandex.com"

    USER_ENABLE_CONFIRM_EMAIL = False
    USER_ENABLE_REMEMBER_ME = False

    USER_LOGIN_TEMPLATE = 'user/login_register.html'
    USER_REGISTER_TEMPLATE = 'user/login_register.html'

    USER_UNAUTHORIZED_ENDPOINT = 'auth_admin'

def create_app():

    app = Flask(__name__)
    app.config.from_object(__name__+'.ConfigClass')
    app.config['UPLOAD_FOLDER'] = os.path.abspath('.') + '/static/products'

    login_manager = LoginManager()
    login_manager.init_app(app)

    babel = Babel(app)

    @babel.localeselector
    def get_locale():
       translations = [str(translation) for translation in babel.list_translations()]

    db = SQLAlchemy(app)

    ''' Database '''
    class User(db.Model, UserMixin):
        __tablename__ = 'users'
        id = db.Column(db.Integer(), primary_key=True)
        active = db.Column('is_active', db.Boolean(), nullable=False, server_default='1')
        email = db.Column(db.String(255, collation='NOCASE'), nullable=False, unique=True)
        email_confirmed_at = db.Column(db.DateTime())
        password = db.Column(db.String(255), nullable=False, server_default='')
        name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')
        phone = db.Column(db.String(30), server_default='')
        roles = db.relationship('Role', secondary='user_roles')

    class Role(db.Model):
        __tablename__ = 'roles'
        id = db.Column(db.Integer(), primary_key=True)
        name = db.Column(db.String(50), unique=True)

    class UserRoles(db.Model):
        __tablename__ = 'user_roles'
        id = db.Column(db.Integer(), primary_key=True)
        user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
        role_id = db.Column(db.Integer(), db.ForeignKey('roles.id', ondelete='CASCADE'))

    class Product(db.Model):
        __tablename__ = 'products'
        id = db.Column(db.Integer(), primary_key=True)
        categories = db.relationship('Category', secondary='products_categories', backref='products')
        image = db.Column(db.String(255), nullable=False, server_default='')
        title = db.Column(db.String(255), nullable=False, server_default='')
        brief = db.Column(db.String(200), server_default='')
        description = db.Column(db.Text(), server_default='')
        price = db.Column(db.Integer(), nullable=False, server_default='')
        create = db.Column(db.DateTime(), default=datetime.utcnow, index=True, nullable=False)

    class Category(db.Model):
        __tablename__ = 'categories'
        id = db.Column(db.Integer(), primary_key=True)
        name = db.Column(db.String(90), unique=True)
        home = db.Column(db.String(5), server_default='0')
        sort = db.Column(db.String(5), server_default='0')

    class ProductsCategory(db.Model):
        __tablename__ = 'products_categories'
        id = db.Column(db.Integer(), primary_key=True)
        category_id = db.Column(db.Integer(), db.ForeignKey('categories.id'))
        product_id = db.Column(db.Integer(), db.ForeignKey('products.id'))

    class Order(db.Model):
        __tablename__ = 'orders'
        id = db.Column(db.Integer(), primary_key=True)
        user_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=True)
        user = db.relationship('User', backref='orders')
        total = db.Column(db.Float(), nullable=False, server_default='0')
        address = db.Column(db.String(200), nullable=False, server_default='')
        payment = db.Column(db.String(60), nullable=False, server_default='Nakit Ödeme')
        status = db.Column(db.String(60), server_default='Hazırlanıyor')
        create = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)

    class OrderItem(db.Model):
        __tablename__ = 'order_items'
        id = db.Column(db.Integer(), primary_key=True)
        name = db.Column(db.String(255), index=True, nullable=False)
        price = db.Column(db.Float(), index=True, nullable=False)
        quantity = db.Column(db.Integer(), index=True, nullable=False)
        order_id = db.Column(db.Integer(), db.ForeignKey('orders.id'), nullable=False)
        order = db.relationship('Order', backref='order_items')
        product_id = db.Column(db.Integer(), db.ForeignKey('products.id'), nullable=False)
        product = db.relationship('Product', backref='order_items')
        cretae = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)

    class Favorite(db.Model):
        __tablename__ = 'favorites'
        id = db.Column(db.Integer(), primary_key=True)
        user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
        user = db.relationship('User', backref='users')
        product_id = db.Column(db.Integer(), db.ForeignKey('products.id', ondelete='CASCADE'))
        product = db.relationship('Product', backref='products')
    ''' Database '''

    class Cart:
        products = {}

    user_manager = UserManager(app, db, User)

    db.create_all()
    engine = create_engine('sqlite:///alisveris.sqlite')
    meta = MetaData(engine).reflect()

    @user_logged_in.connect_via(app)
    def _after_login_hook(sender, user, **extra):
        ''' Kullanıcı Giriş Yaptı '''

    @user_logged_out.connect_via(app)
    def _after_logout_hook(sender, user, **extra):
        ''' Kullanıcı Çıkış Yaptı '''
        Cart.products = {}

    def allowed_file(filename):
        ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
        return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    def upload_image(request):
        status = {}
        if request.method == 'POST':
            if 'file' not in request.files:
                status = {'status':'error', 'file':'Dosya Bulunamadı!..'}

            file = request.files['file']
            if file.filename == '':
                status = {'status':'error', 'file':'Dosya seçilmedi!..'}
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                status = {'status':'success', 'file':filename}
        return status

    ''' Varsayılan Kullanıcı Bilgileri '''
    if not User.query.filter(User.email == 'mymucahityilmaz@hotmail.com').first():
        user = User(
            name = 'Mücahit YILMAZ',
            phone = '05556868524',
            email = 'mymucahityilmaz@hotmail.com',
            email_confirmed_at = datetime.utcnow(),
            password = user_manager.hash_password('2019mucahit')
        )
        db.session.add(user)
        db.session.commit()

    if not User.query.filter(User.email == 'admin@admin.com').first():
        user = User(
            name = 'Admin',
            phone = '05556868524',
            email = 'admin@admin.com',
            email_confirmed_at = datetime.utcnow(),
            password = user_manager.hash_password('2020admin')
        )
        user.roles.append(Role(name='Admin'))
        db.session.add(user)
        db.session.commit()
    ''' Varsayılan Kullanıcı Bilgileri '''

    ''' Herkese Açık Linkler '''
    @app.route('/')
    def index():
        products = Product.query.order_by(Product.title).limit(40).all()
        categories = Category.query.order_by(Category.sort).all()
        hcategories = Category.query.filter_by(home='1').order_by(Category.sort).all()
        return render_template('index.html', products = products, categories = categories, hcategories = hcategories)

    @app.route('/iletisim')
    def iletisim():
        return render_template('contact.html')

    @app.route('/kategori/<kategoriID>/<KategoriAdi>')
    def kategori_detay(kategoriID, KategoriAdi):
        category = Category.query.filter_by(id=kategoriID).first()
        order = Product.id
        sort = request.args.get('sort', '')
        if sort == 'eskiden':
            order = Product.create
        if sort == 'yeniden':
            order = desc(Product.create)
        if sort == 'fiyatArtan':
            order = Product.price
        if sort == 'fiyatAzalan':
            order = desc(Product.price)
        products = Product.query.filter(Product.categories.any(id=kategoriID)).order_by(order).all()
        return render_template('category.html', categoryName = category.name, products = products)

    @app.route('/urun/<urunID>/<urunAdi>')
    def urun_detay(urunID, urunAdi):
        product = Product.query.filter_by(id=int(urunID)).order_by(desc(Product.id)).first()
        if product is None:
            return redirect('/')
        return render_template('single-product.html', productID = urunID, product = product)

    @app.route('/giris', methods = ['GET', 'POST'])
    def giris():
        sonuc = {}
        if current_user.is_authenticated:
            return redirect('/hesabim')
        if request.method == 'POST':
            email = request.form['eposta']
            password = request.form['pass']
            user = User.query.filter_by(email=email).first()
            if not user or not user_manager.verify_password(password, user.password):
                flash('Eposta adresi veya şifreniz hatalı/eksik!..')
                return render_template('user/login_register.html', sonuc = sonuc)
            else :
                login_user(user, remember=True)
                flash('Başarıyla giriş yapıldı')
                next = request.form['next']
                return redirect(next or url_for('hesabim'))
        return render_template('user/login_register.html', sonuc = sonuc)

    @app.route('/kayit', methods = ['GET', 'POST'])
    def kayit():
        sonuc = {}
        if current_user.is_authenticated:
            return redirect('/hesabim')
        if request.method == 'POST':
            fullname = request.form['name']
            phone = request.form['phone']
            email = request.form['email']
            password = request.form['pass']
            existing_user = User.query.filter_by(email=email).first()
            if existing_user is None:
                user = User(
                    name = fullname,
                    phone = phone,
                    email = email,
                    email_confirmed_at = datetime.utcnow(),
                    password = user_manager.hash_password(password)
                )
                db.session.add(user)
                db.session.commit()
                flash('Başarıyla kayıt olundu, Giriş yapabilirsiniz')
                return redirect('/giris')
            else :
                flash('Kayıt olurken hata oluştu, lütfen kayıt formunu eksiksiz doldurunuz..')
        return redirect('/giris')
    ''' Jquery '''
    @app.route('/header_category', methods=['POST'])
    def header_category():
        category = {}
        categories = Category.query.order_by(Category.sort).all()
        for cat in categories:
            category[cat.id] = cat.name
        return category

    @app.route('/favori_say', methods=['POST'])
    def favori_say():
        fav_count = 0
        if current_user.is_authenticated:
            fav_count = Favorite.query.filter_by(user_id=current_user.id).count()
        return str(fav_count)

    @app.route('/favori_ekle', methods=['POST'])
    def favori_ekle():
        sonuc = ''
        if current_user.is_authenticated:
            userFavori = Favorite.query.filter_by(product_id=int(request.form['id'])).first()
            if userFavori is None:
                fav = Favorite(user_id = current_user.id, product_id = int(request.form['id']) )
                db.session.add(fav)
                db.session.commit()
                sonuc = 'Eklendi'
            else :
                sonuc = 'Zaten Ekli'
        else :
            sonuc = 'Lütfen Üye Girişi Yapınız'
        return sonuc

    ''' Sepet İşlemleri '''
    @app.route('/sepet_listele', methods=['POST'])
    def sepet_listele():
        return Cart.products

    @app.route('/sepete_ekle/<EkleUrunID>', methods=['POST'])
    def sepete_ekle(EkleUrunID):
        urun = request.form['id'];
        if urun in Cart.products:
            sonuc = 'zaten ekli'
        else :
            Cart.products[urun] = {
                'id': urun,
                'adi': request.form['adi'],
                'fiyat': float(request.form['fiyat']),
                'adet': int(request.form['adet']),
                'toplam': float(request.form['fiyat']) * int(request.form['adet'])
            }
            sonuc = 'eklendi'
        return sonuc

    @app.route('/sepetten_cikar/<CikarUrunID>', methods=['POST'])
    def sepetten_cikar(CikarUrunID):
        urun_sil = request.form['id'];
        del Cart.products[urun_sil]
        sonuc = 'silindi'
        if urun_sil in Cart.products:
            sonuc = 'basarisiz'
        return sonuc
    ''' Sepet İşlemleri '''

    ''' Üyelere Açık Linkler '''
    @app.route('/hesabim')
    @login_required
    def hesabim():
        return render_template('user/account.html')

    @app.route('/hesabim/siparislerim')
    @login_required
    def hesabim_siparislerim():
        orders = Order.query.filter_by(user_id=int(current_user.id)).order_by(desc(Order.id)).all()
        return render_template('user/orders.html', orders = orders)

    @app.route('/hesabim/siparis/<id>')
    @login_required
    def hesabim_siparis_id(id):
        order_detail = Order.query.filter_by(id=int(id)).first()
        order_items = OrderItem.query.filter_by(order_id=int(order_detail.id)).all()
        return render_template('user/order-detail.html', order_detail = order_detail, order_items = order_items)

    @app.route('/hesabim/siparisiptal/<id>')
    @roles_required('Admin')
    def hesabim_siparisiptal(id):
        order = Order.query.filter_by(id=int(id)).first()
        if order is not None:
            order.status = 'İptal Edildi'
            db.session.commit()
            flash('Siparişiniz iptal edildi..')
        else :
            flash('Sipariş bilgisi güncellenemiyor, lütfen daha sonra tekrar deneyiniz..')
        return redirect('/hesabim/siparislerim')

    @app.route('/hesabim/blgilerim')
    @login_required
    def hesabim_bilgilerim():
        user = User.query.filter_by(id=int(current_user.id)).first()
        return render_template('user/info.html', user = user)

    @app.route('/hesabim/bilgiguncelle', methods = ['POST'])
    @login_required
    def hesabim_bilgiguncelle():
        if request.method == 'POST':
            user = User.query.filter_by(id=int(current_user.id)).first()
            if user is not None:
                user.name = request.form['adi']
                user.email = request.form['eposta']
                user.phone = request.form['tel']
                if request.form['sifre'] != '':
                    if request.form['sifre'] == request.form['tsifre']:
                        password = request.form['sifre']
                        user.password = user_manager.hash_password(password)
                    else :
                        flash('Şifreler aynı değil, birbiriyle uyuşmuyor!..')
                        return redirect('/hesabim/bilgilerm')
                db.session.commit()
                flash('Bilgileriniz başarıyla güncellendi..')
        return redirect('/hesabim')

    @app.route('/hesabim/favorilerim')
    @login_required
    def hesabim_favorilerim():
        favoriler = Favorite.query.filter_by(user_id=int(current_user.id)).all()
        return render_template('user/wishlist.html', favoriler = favoriler)

    @app.route('/hesabim/favorisil/<fav_id>')
    @login_required
    def hesabim_favorisil(fav_id):
        delete = Favorite.query.filter_by(id=int(fav_id)).first()
        title = delete.product.title
        db.session.delete(delete)
        db.session.commit()
        flash(title + ' ürünü favorilerinizden çıkarıldı')
        return redirect('/hesabim/favorilerim')

    @app.route('/sepet')
    #@login_required
    def sepet():
        return render_template('cart.html', items = Cart.products)

    @app.route('/odeme')
    @login_required
    def odeme():
        if len(Cart.products) < 1:
            return redirect('/')
        return render_template('checkout.html', items = Cart.products)

    @app.route('/odeme-tamamla', methods = ['POST'])
    @login_required
    def odeme_tamamla():
        if len(Cart.products) < 1:
            flash('Sepetiniz Boş!.')
            return redirect('/hesabim')
        if request.method == 'POST':
            odeme = request.form['odeme']
            yeni_siparis = Order(
                user_id = current_user.id,
                total = float(request.form['toplam']),
                address = request.form['adi'] + '<br>'+request.form['tel']+'<br>' + request.form['adres'] + ' ' + request.form['sehir'] + ' / ' + request.form['ulke'],
                payment = odeme,
                status = 'Hazırlanıyor'
            )
            product_ids = []
            for i in Cart.products:
                product_ids.append(int(Cart.products[i]['id']))
            products = db.session.query(Product).filter(Product.id.in_(product_ids)).all()
            for index, product in enumerate(products):
                yeni_siparis.order_items.append(
                    OrderItem(
                        name = product.title,
                        price = product.price,
                        quantity = Cart.products[str(product.id)]['adet'],
                        product=product
                    )
                )
            db.session.add(yeni_siparis)
            db.session.commit()
            Cart.products = {}
            #flash('Siparişiniz başarıyla tamamlandı..')
            if odeme == 'Kredi Kartı':
                return render_template('credi-card.html', toplam = float(request.form['toplam']))
            return redirect('/odeme/basarili')
        return redirect('/odeme')

    @app.route('/odeme/basarili')
    @login_required
    def odeme_basarili():
        return render_template('success.html')

    @app.route('/auth_admin')
    @login_required
    def auth_admin():
        return redirect('/hesabim?auth=admin')

    @app.route('/cikis')
    @login_required
    def user_logout():
        logout_user()
        Cart.products = {}
        return redirect('/')

    ''' Yöneticilere Açık Linkler '''
    @app.route('/admin')
    @roles_required('Admin')
    def admin():
        orders = Order.query.order_by(desc(Order.id)).all()
        return render_template('admin/index.html', activaTab = 'siparisler', orders = orders)

    @app.route('/admin/siparis/<id>')
    @roles_required('Admin')
    def admin_siparis(id):
        order_detail = Order.query.filter_by(id=int(id)).first()
        order_items = OrderItem.query.filter_by(order_id=int(order_detail.id)).all()
        return render_template('admin/index.html', activaTab = 'siparis_detay', order_detail = order_detail, order_items = order_items)

    @app.route('/admin/siparistamamla', methods = ['POST'])
    @roles_required('Admin')
    def admin_siparistamamla():
        if request.method == 'POST':
            siparis_id = request.form['siparis_id']
            order = Order.query.filter_by(id=int(siparis_id)).first()
            if order is not None:
                order.status = request.form['siparis_durumu']
                db.session.commit()
                flash('Sipariş bilgisi başarıyla güncellendi..')
            else :
                flash('Sipariş bilgisi güncellenemiyor, lütfen daha sonra tekrar deneyiniz..')
        return redirect('/admin/siparis/'+siparis_id)

    @app.route('/admin/siparissil/<siparis_id>', methods=['GET'])
    @roles_required('Admin')
    def admin_siparissil(siparis_id):
        order_items = OrderItem.query.filter_by(order_id=int(siparis_id)).all()
        for item in order_items:
            db.session.delete(item)
        delete = Order.query.filter_by(id=int(siparis_id)).first()
        db.session.delete(delete)
        db.session.commit()
        flash('Sipariş başarıyla silindi')
        return redirect('/admin')

    @app.route('/admin/urunler')
    @roles_required('Admin')
    def admin_urunler():
        activaTab = 'urunler'
        product = ''
        products = Product.query.order_by(desc(Product.id)).all()
        categories = Category.query.order_by(Category.id).all()
        if 'duzenle' in request.args:
            activaTab = 'duzenle'
            product = Product.query.filter_by(id=int(request.args.get('duzenle'))).first()
        return render_template('admin/products.html', products = products, categories = categories, activaTab = activaTab, product = product)

    @app.route('/admin/urunekle', methods=['POST'])
    @roles_required('Admin')
    def admin_urunekle():
        result = {'status':'error'}
        if request.method == 'POST':
            result = upload_image(request)
            if result['status'] == 'success':
                urun_resim = result['file']
            else:
                urun_resim = ''
                flash('Ürün fotoğrafı yüklenemedi, Daha sonra tekrar deneyiniz..')
                return redirect('/admin/urunler')
            urun_adi = request.form['urun_adi']
            urun_fiyat = float(request.form['urun_fiyat'])
            urun_onaciklama = request.form['urun_onaciklama']
            urun_aciklama = request.form['urun_aciklama']
            urun_kategori = request.form['urun_kategori']
            yeni_urun = Product(
                title = urun_adi,
                brief = urun_onaciklama,
                description = urun_aciklama,
                image = urun_resim,
                price = urun_fiyat
            )
            yeni_cate = Category.query.filter_by(id=int(urun_kategori)).first()
            yeni_urun.categories.append(yeni_cate)
            db.session.add(yeni_urun)
            db.session.commit()
            flash('Ürün başarıyla eklendi..')
        return redirect('/admin/urunler')

    @app.route('/admin/urunguncelle', methods=['POST'])
    @roles_required('Admin')
    def admin_urunguncelle():
        result = {'status':'error'}
        if request.method == 'POST':
            result = upload_image(request)
            exists_product = Product.query.filter_by(id=int(request.form['urun_id_duzenle'])).first()
            if result['status'] == 'success':
                urun_resim = result['file']
                if exists_product is not None:
                    exists_product.image = urun_resim
            else:
                urun_resim = ''
            if exists_product is not None:
                exists_product.title = request.form['urun_adi_duzenle']
                exists_product.price = request.form['urun_fiyat_duzenle']
                exists_product.brief = request.form['urun_onaciklama_duzenle']
                exists_product.description = request.form['urun_aciklama_duzenle']
                update_cate = Category.query.filter_by(id=int(request.form['urun_kategori_duzenle'])).first()
                exists_product.categories = [update_cate]
                db.session.commit()
            flash('Ürün başarıyla güncellendi..')
        return redirect('/admin/urunler')

    @app.route('/admin/urunsil/<urun_id>', methods=['GET'])
    @roles_required('Admin')
    def admin_urunsil(urun_id):
        delete = Product.query.filter_by(id=int(urun_id)).first()
        delete_img = os.path.join(app.config['UPLOAD_FOLDER'], delete.image)
        if os.path.exists(delete_img):
            os.remove(delete_img)
        db.session.delete(delete)
        db.session.commit()
        flash('Ürün başarıyla silindi')
        return redirect('/admin/urunler')

    @app.route('/admin/kategoriler', methods = ['GET', 'POST'])
    @roles_required('Admin')
    def admin_kategoriler():
        if request.method == 'POST':
            if request.form['action'] == 'yeni':
                cat = Category(
                    name = request.form['kategori_adi'],
                    home = request.form['kategori_home'],
                    sort = request.form['kategori_sira']
                )
                db.session.add(cat)
                db.session.commit()
            if request.form['action'] == 'guncelle':
                guncelle = Category.query.filter_by(id=int(request.form['kategori_id'])).first()
                guncelle.name = request.form['kategori_adi']
                guncelle.home = request.form['kategori_home']
                guncelle.sort = request.form['kategori_sira']
                db.session.commit()
        categories = Category.query.order_by(Category.sort).all()
        return render_template('admin/categories.html', categories = categories)

    @app.route('/admin/kategori/sil/<kategori_id>',)
    @roles_required('Admin')
    def admin_kategori_sil(kategori_id):
        delete = Category.query.filter_by(id=int(kategori_id)).first()
        db.session.delete(delete)
        db.session.commit()
        return redirect('/admin/kategoriler')

    @app.route('/admin/kullanicilar')
    @roles_required('Admin')
    def admin_kullanicilar():
        users = User.query.order_by(User.id).all()
        return render_template('admin/users.html', users = users)

    @app.route('/admin/kullanici_sil/<kullanici_id>',)
    @roles_required('Admin')
    def admin_kullanici_sil(kullanici_id):
        orders = Order.query.filter_by(user_id=int(kullanici_id)).all()
        for order in orders:
            order_items = OrderItem.query.filter_by(order_id=int(order.id)).all()
            for item in order_items:
                db.session.delete(item)
            db.session.delete(order)
        delete = User.query.filter_by(id=int(kullanici_id)).first()
        db.session.delete(delete)
        db.session.commit()
        return redirect('/admin/kullanicilar')

    ''' Admin İşlemler '''


    return app

if __name__ == '__main__':
    app = create_app()
    app.run(port=5050, debug=True)
