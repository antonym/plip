# plip
It's a small layer between servers booting via iPXE and Craton.  It converts variables from Craton into variables iPXE and read:

* Server boots iPXE and pulls DHCP address
* iPXE calls out to plip
* plip calls out to Craton to get details about the server
* plip returns iPXE variables and a script so the server can boot

## Running plip
To run plip, you'll need the flask python module:

    pip install flask
    git clone git@github.com:antonym/plip.git
    ./plip.py

For plip to work properly, you must put your Craton authentication credentials and Craton endpoint URL into config.py:

*config.py:*

    craton_url = 'http://craton.url.here:7780/v1'
    craton_creds = {
        'username': 'your_sso_username',
        'password': 'your_craton_password',
        'project': 'your_project_id'
    }

There is a wsgi file supplied as well in case you want to run the application along with mod_wsgi and an apache server.  Here's a sample apache configuration that you could add to a virtual host block:

    WSGIDaemonProcess plip user=plip group=plip processes=50
    WSGIScriptAlias / /var/www/plip/plip.wsgi

    <Directory /var/www/plip>
        WSGIProcessGroup plip
        WSGIApplicationGroup %{GLOBAL}
        Order deny,allow
        Allow from all
    </Directory>

## Using plip
If you access the application without any characters after the URL (like http://example.com/), you can enter data into a form.  Here's what a sample full search URL might look like:

    http://[plip_server_ip]/pxe?switch_name=A2-25-1.dfw2&switch_port=Gi1/9

## Optional Parameters

### debug
Debugging is disabled by default.  If you enable debugging with `debug=yes` in the query string, plip will append the json dump from Craton to end of the iPXE file.  This could be useful for troubleshooting.
