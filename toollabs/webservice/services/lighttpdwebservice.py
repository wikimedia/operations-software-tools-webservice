import os
from toollabs.webservice import WebService


BASIC_CONFIG_TEMPLATE = """
server.modules = (
  "mod_setenv",
  "mod_access",
  "mod_accesslog",
  "mod_alias",
  "mod_compress",
  "mod_redirect",
  "mod_rewrite",
  "mod_fastcgi",
  "mod_cgi",
)

server.port = {port}
server.use-ipv6 = "disable"
server.username = "{username}"
server.groupname = "{groupname}"
server.core-files = "disable"
server.document-root = "{home}/public_html"
server.pid-file = "/var/run/lighttpd/{toolname}.pid"
server.errorlog = "{home}/error.log"
server.breakagelog = "{home}/error.log"
server.follow-symlink = "enable"
server.max-connections = 300
server.stat-cache-engine = "simple"
server.event-handler = "linux-sysepoll"
ssl.engine = "disable"

alias.url = ( "/{toolname}" => "{home}/public_html/" )

index-file.names = ( "index.php", "index.html", "index.htm" )
dir-listing.encoding = "utf-8"
server.dir-listing = "disable"
url.access-deny = ( "~", ".inc" )
static-file.exclude-extensions = ( ".php", ".pl", ".fcgi" )

accesslog.use-syslog = "disable"
accesslog.filename = "{home}/access.log"

include_shell "/usr/share/lighttpd/create-mime.assign.pl"

cgi.assign = (
  ".pl" => "/usr/bin/perl",
  ".py" => "/usr/bin/python",
  ".pyc" => "/usr/bin/python",
)
"""

ENABLE_PHP_CONFIG_TEMPLATE = """
fastcgi.server += ( ".php" =>
        ((
                "bin-path" => "/usr/bin/php-cgi",
                "socket" => "/var/run/lighttpd/php.socket.{toolname}",
                "max-procs" => 2,
                "bin-environment" => (
                        "PHP_FCGI_CHILDREN" => "2",
                        "PHP_FCGI_MAX_REQUESTS" => "500"
                ),
                "bin-copy-environment" => (
                        "PATH", "SHELL", "USER"
                ),
                "broken-scriptfilename" => "enable",
                "allow-x-send-file" => "enable"
         ))
)
"""


class LighttpdPlainWebService(WebService):
    """
    A 'plain' Lighttpd Webserver, without PHP setup by default
    """
    NAME = 'lighttpd-plain'
    QUEUE = 'webgrid-lighttpd'

    def check(self):
        # Check for a .lighttpd.conf file or a public_html
        public_html_path = self.tool.get_homedir_subpath('public_html')
        lighttpd_conf_path = self.tool.get_homedir_subpath('.lighttpd.conf')
        if not (
            os.path.exists(public_html_path) or
            os.path.exists(lighttpd_conf_path)
        ):
            raise WebService.InvalidWebServiceException(
                'Could not find a public_html folder or a .lighttpd.conf '
                'file in your tool home.'
            )

    def build_config(self, port, config_template=BASIC_CONFIG_TEMPLATE):
        config = config_template.format(
            toolname=self.tool.name,
            username=self.tool.username,
            groupname=self.tool.username,
            home=self.tool.home,
            port=port
        )
        try:
            with open(self.tool.get_homedir_subpath('.lighttpd.conf')) as f:
                config += f.read()
        except IOError:
            pass  # No customized file, not a big deal
        return config

    def run(self, port):
        config = self.build_config(port)
        config_path = os.path.join('/var/run/lighttpd/', self.tool.name)
        with open(config_path, 'w') as f:
            f.write(config)

        os.execv(
            '/usr/sbin/lighttpd',
            ['/usr/sbin/lighttpd', '-f', config_path, '-D'])


class LighttpdWebService(LighttpdPlainWebService):
    """
    A Lighttpd Webserver with a default PHP setup
    """
    NAME = 'lighttpd'
    QUEUE = 'webgrid-lighttpd'

    def build_config(
        self, port,
        config_template=BASIC_CONFIG_TEMPLATE + ENABLE_PHP_CONFIG_TEMPLATE
    ):
        return super(LighttpdWebService, self).build_config(
            port, config_template)
