apt-get install                 \
    apache2                     \
    mysql-server                \
    libapache2-mod-wsgi         \
    libapache2-mod-jk           \
    python-cjson                \
    python-django               \
    python-django-piston        \
    python-mysqldb              \
    python-libxml2              \
    python-lxml                 \
    python-django-extensions    \
    python-django-extra-views   \
    python-imaging              \
    sqlite3                     \
    javascript-common           \
    libjs-jquery-ui             \
    libjs-jquery-timepicker
echo 'export MDS_DIR=/opt/sana/sana.mds' >> /etc/apache2/envvars
adduser django
usermod -a -G django www-data
mkdir -p /opt/sana/cache                \
    /opt/sana/sana.mds/cache/media      \
    /opt/sana/sana.mds/cache/static     \
    /opt/sana/sana.mds/cache/db
ln -s /home/django/git/sana.mds/src /opt/sana/sana.mds/mds
mysql -u root -p
cp ../include/mds/apache2/conf-available/mds.conf /etc/apache2/conf-available/
cp ../include/mds/apache2/conf-available/openmrs.conf /etc/apache2/conf-available/
a2enconf mds
a2enconf openmrs
cp ../src/mds/settings.py.tmpl ../src/mds/settings.py
cp ../src/mds/local_settings.py.tmpl ../src/mds/local_settings.py
