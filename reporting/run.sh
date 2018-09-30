#generate a random URL to serve content from
UID=`dd if=/dev/urandom count=4 bs=1 | md5sum | cut -d" " -f1`
sed -i -e "s|UID|$UID|g" /etc/nginx/conf.d/default.conf
echo "Reporting Server: serving reports on http://localhost/$UID"
nginx -g "daemon off;"
