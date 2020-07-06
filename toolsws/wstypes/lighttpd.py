import os

from .ws import WebService


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

index-file.names = ( "index.php", "index.html", "index.htm" )
dir-listing.encoding = "utf-8"
server.dir-listing = "disable"
url.access-deny = ( "~", ".inc" )
static-file.exclude-extensions = ( ".php", ".pl", ".fcgi" )

accesslog.use-syslog = "disable"

# no longer enabled by default (T233347)
# accesslog.filename = "{home}/access.log"

mimetype.assign = (
  ".pcf.Z" => "application/x-font-pcf",
  ".tar.bz2" => "application/x-gtar-compressed",
  ".tar.gz" => "application/x-gtar-compressed",
  ".ez" => "application/andrew-inset",
  ".anx" => "application/annodex",
  ".atom" => "application/atom+xml",
  ".atomcat" => "application/atomcat+xml",
  ".atomsrv" => "application/atomserv+xml",
  ".lin" => "application/bbolin",
  ".cu" => "application/cu-seeme",
  ".davmount" => "application/davmount+xml",
  ".dcm" => "application/dicom",
  ".tsp" => "application/dsptype",
  ".es" => "application/ecmascript",
  ".pfr" => "application/font-tdpfr",
  ".spl" => "application/futuresplash",
  ".gz" => "application/gzip",
  ".hta" => "application/hta",
  ".jar" => "application/java-archive",
  ".ser" => "application/java-serialized-object",
  ".class" => "application/java-vm",
  ".js" => "application/javascript; charset=utf-8",
  ".json" => "application/json; charset=utf-8",
  ".m3g" => "application/m3g",
  ".hqx" => "application/mac-binhex40",
  ".cpt" => "application/mac-compactpro",
  ".nb" => "application/mathematica",
  ".nbp" => "application/mathematica",
  ".mbox" => "application/mbox",
  ".mdb" => "application/msaccess",
  ".doc" => "application/msword",
  ".dot" => "application/msword",
  ".mxf" => "application/mxf",
  ".asn" => "application/octet-stream",
  ".bin" => "application/octet-stream",
  ".deploy" => "application/octet-stream",
  ".ent" => "application/octet-stream",
  ".msp" => "application/octet-stream",
  ".msu" => "application/octet-stream",
  ".oda" => "application/oda",
  ".opf" => "application/oebps-package+xml",
  ".ogx" => "application/ogg",
  ".one" => "application/onenote",
  ".onepkg" => "application/onenote",
  ".onetmp" => "application/onenote",
  ".onetoc2" => "application/onenote",
  ".pdf" => "application/pdf",
  ".pgp" => "application/pgp-encrypted",
  ".key" => "application/pgp-keys",
  ".sig" => "application/pgp-signature",
  ".prf" => "application/pics-rules",
  ".ai" => "application/postscript",
  ".eps" => "application/postscript",
  ".eps2" => "application/postscript",
  ".eps3" => "application/postscript",
  ".epsf" => "application/postscript",
  ".epsi" => "application/postscript",
  ".ps" => "application/postscript",
  ".rar" => "application/rar",
  ".rdf" => "application/rdf+xml",
  ".rtf" => "application/rtf",
  ".stl" => "application/sla",
  ".smi" => "application/smil+xml",
  ".smil" => "application/smil+xml",
  ".xht" => "application/xhtml+xml",
  ".xhtml" => "application/xhtml+xml",
  ".xml" => "application/xml",
  ".xsd" => "application/xml",
  ".dtd" => "application/xml-dtd",
  ".xsl" => "application/xslt+xml",
  ".xslt" => "application/xslt+xml",
  ".xspf" => "application/xspf+xml",
  ".zip" => "application/zip",
  ".apk" => "application/vnd.android.package-archive",
  ".cdy" => "application/vnd.cinderella",
  ".ddeb" => "application/vnd.debian.binary-package",
  ".deb" => "application/vnd.debian.binary-package",
  ".udeb" => "application/vnd.debian.binary-package",
  ".sfd" => "application/vnd.font-fontforge-sfd",
  ".kml" => "application/vnd.google-earth.kml+xml",
  ".kmz" => "application/vnd.google-earth.kmz",
  ".xul" => "application/vnd.mozilla.xul+xml",
  ".xlb" => "application/vnd.ms-excel",
  ".xls" => "application/vnd.ms-excel",
  ".xlt" => "application/vnd.ms-excel",
  ".xlam" => "application/vnd.ms-excel.addin.macroEnabled.12",
  ".xlsb" => "application/vnd.ms-excel.sheet.binary.macroEnabled.12",
  ".xlsm" => "application/vnd.ms-excel.sheet.macroEnabled.12",
  ".xltm" => "application/vnd.ms-excel.template.macroEnabled.12",
  ".eot" => "application/vnd.ms-fontobject",
  ".thmx" => "application/vnd.ms-officetheme",
  ".cat" => "application/vnd.ms-pki.seccat",
  ".pps" => "application/vnd.ms-powerpoint",
  ".ppt" => "application/vnd.ms-powerpoint",
  ".ppam" => "application/vnd.ms-powerpoint.addin.macroEnabled.12",
  ".pptm" => "application/vnd.ms-powerpoint.presentation.macroEnabled.12",
  ".sldm" => "application/vnd.ms-powerpoint.slide.macroEnabled.12",
  ".ppsm" => "application/vnd.ms-powerpoint.slideshow.macroEnabled.12",
  ".potm" => "application/vnd.ms-powerpoint.template.macroEnabled.12",
  ".docm" => "application/vnd.ms-word.document.macroEnabled.12",
  ".dotm" => "application/vnd.ms-word.template.macroEnabled.12",
  ".odc" => "application/vnd.oasis.opendocument.chart",
  ".odb" => "application/vnd.oasis.opendocument.database",
  ".odf" => "application/vnd.oasis.opendocument.formula",
  ".odg" => "application/vnd.oasis.opendocument.graphics",
  ".otg" => "application/vnd.oasis.opendocument.graphics-template",
  ".odi" => "application/vnd.oasis.opendocument.image",
  ".odp" => "application/vnd.oasis.opendocument.presentation",
  ".otp" => "application/vnd.oasis.opendocument.presentation-template",
  ".ods" => "application/vnd.oasis.opendocument.spreadsheet",
  ".ots" => "application/vnd.oasis.opendocument.spreadsheet-template",
  ".odt" => "application/vnd.oasis.opendocument.text",
  ".odm" => "application/vnd.oasis.opendocument.text-master",
  ".ott" => "application/vnd.oasis.opendocument.text-template",
  ".oth" => "application/vnd.oasis.opendocument.text-web",
  ".cod" => "application/vnd.rim.cod",
  ".mmf" => "application/vnd.smaf",
  ".sdc" => "application/vnd.stardivision.calc",
  ".sds" => "application/vnd.stardivision.chart",
  ".sda" => "application/vnd.stardivision.draw",
  ".sdd" => "application/vnd.stardivision.impress",
  ".sdf" => "application/vnd.stardivision.math",
  ".sdw" => "application/vnd.stardivision.writer",
  ".sgl" => "application/vnd.stardivision.writer-global",
  ".sxc" => "application/vnd.sun.xml.calc",
  ".stc" => "application/vnd.sun.xml.calc.template",
  ".sxd" => "application/vnd.sun.xml.draw",
  ".std" => "application/vnd.sun.xml.draw.template",
  ".sxi" => "application/vnd.sun.xml.impress",
  ".sti" => "application/vnd.sun.xml.impress.template",
  ".sxm" => "application/vnd.sun.xml.math",
  ".sxw" => "application/vnd.sun.xml.writer",
  ".sxg" => "application/vnd.sun.xml.writer.global",
  ".stw" => "application/vnd.sun.xml.writer.template",
  ".sis" => "application/vnd.symbian.install",
  ".cap" => "application/vnd.tcpdump.pcap",
  ".pcap" => "application/vnd.tcpdump.pcap",
  ".vsd" => "application/vnd.visio",
  ".vss" => "application/vnd.visio",
  ".vst" => "application/vnd.visio",
  ".vsw" => "application/vnd.visio",
  ".wbxml" => "application/vnd.wap.wbxml",
  ".wmlc" => "application/vnd.wap.wmlc",
  ".wmlsc" => "application/vnd.wap.wmlscriptc",
  ".wpd" => "application/vnd.wordperfect",
  ".wp5" => "application/vnd.wordperfect5.1",
  ".wk" => "application/x-123",
  ".7z" => "application/x-7z-compressed",
  ".abw" => "application/x-abiword",
  ".dmg" => "application/x-apple-diskimage",
  ".bcpio" => "application/x-bcpio",
  ".torrent" => "application/x-bittorrent",
  ".bz2" => "application/x-bzip",
  ".cab" => "application/x-cab",
  ".cbr" => "application/x-cbr",
  ".cbz" => "application/x-cbz",
  ".cda" => "application/x-cdf",
  ".cdf" => "application/x-cdf",
  ".vcd" => "application/x-cdlink",
  ".pgn" => "application/x-chess-pgn",
  ".mph" => "application/x-comsol",
  ".cpio" => "application/x-cpio",
  ".dcr" => "application/x-director",
  ".dir" => "application/x-director",
  ".dxr" => "application/x-director",
  ".dms" => "application/x-dms",
  ".wad" => "application/x-doom",
  ".dvi" => "application/x-dvi",
  ".gsf" => "application/x-font",
  ".pfa" => "application/x-font",
  ".pfb" => "application/x-font",
  ".pcf" => "application/x-font-pcf",
  ".mm" => "application/x-freemind",
  ".gan" => "application/x-ganttproject",
  ".gnumeric" => "application/x-gnumeric",
  ".sgf" => "application/x-go-sgf",
  ".gcf" => "application/x-graphing-calculator",
  ".gtar" => "application/x-gtar",
  ".taz" => "application/x-gtar-compressed",
  ".tbz" => "application/x-gtar-compressed",
  ".tgz" => "application/x-gtar-compressed",
  ".hdf" => "application/x-hdf",
  ".hwp" => "application/x-hwp",
  ".ica" => "application/x-ica",
  ".info" => "application/x-info",
  ".ins" => "application/x-internet-signup",
  ".isp" => "application/x-internet-signup",
  ".iii" => "application/x-iphone",
  ".iso" => "application/x-iso9660-image",
  ".jam" => "application/x-jam",
  ".jnlp" => "application/x-java-jnlp-file",
  ".jmz" => "application/x-jmol",
  ".chrt" => "application/x-kchart",
  ".kil" => "application/x-killustrator",
  ".skd" => "application/x-koan",
  ".skm" => "application/x-koan",
  ".skp" => "application/x-koan",
  ".skt" => "application/x-koan",
  ".kpr" => "application/x-kpresenter",
  ".kpt" => "application/x-kpresenter",
  ".ksp" => "application/x-kspread",
  ".kwd" => "application/x-kword",
  ".kwt" => "application/x-kword",
  ".latex" => "application/x-latex",
  ".lha" => "application/x-lha",
  ".lyx" => "application/x-lyx",
  ".lzh" => "application/x-lzh",
  ".lzx" => "application/x-lzx",
  ".book" => "application/x-maker",
  ".fb" => "application/x-maker",
  ".fbdoc" => "application/x-maker",
  ".fm" => "application/x-maker",
  ".frame" => "application/x-maker",
  ".frm" => "application/x-maker",
  ".maker" => "application/x-maker",
  ".mif" => "application/x-mif",
  ".m3u8" => "application/x-mpegURL",
  ".application" => "application/x-ms-application",
  ".manifest" => "application/x-ms-manifest",
  ".wmd" => "application/x-ms-wmd",
  ".wmz" => "application/x-ms-wmz",
  ".bat" => "application/x-msdos-program",
  ".com" => "application/x-msdos-program",
  ".dll" => "application/x-msdos-program",
  ".exe" => "application/x-msdos-program",
  ".msi" => "application/x-msi",
  ".nc" => "application/x-netcdf",
  ".pac" => "application/x-ns-proxy-autoconfig",
  ".nwc" => "application/x-nwc",
  ".o" => "application/x-object",
  ".oza" => "application/x-oz-application",
  ".p7r" => "application/x-pkcs7-certreqresp",
  ".crl" => "application/x-pkcs7-crl",
  ".pyc" => "application/x-python-code",
  ".pyo" => "application/x-python-code",
  ".qgs" => "application/x-qgis",
  ".shp" => "application/x-qgis",
  ".shx" => "application/x-qgis",
  ".qtl" => "application/x-quicktimeplayer",
  ".rdp" => "application/x-rdp",
  ".rpm" => "application/x-redhat-package-manager",
  ".rss" => "application/x-rss+xml",
  ".rb" => "application/x-ruby",
  ".sce" => "application/x-scilab",
  ".sci" => "application/x-scilab",
  ".xcos" => "application/x-scilab-xcos",
  ".shar" => "application/x-shar",
  ".swf" => "application/x-shockwave-flash",
  ".swfl" => "application/x-shockwave-flash",
  ".scr" => "application/x-silverlight",
  ".sql" => "application/x-sql",
  ".sit" => "application/x-stuffit",
  ".sitx" => "application/x-stuffit",
  ".sv4cpio" => "application/x-sv4cpio",
  ".sv4crc" => "application/x-sv4crc",
  ".tar" => "application/x-tar",
  ".gf" => "application/x-tex-gf",
  ".pk" => "application/x-tex-pk",
  ".texi" => "application/x-texinfo",
  ".texinfo" => "application/x-texinfo",
  ".roff" => "application/x-troff",
  ".t" => "application/x-troff",
  ".tr" => "application/x-troff",
  ".man" => "application/x-troff-man",
  ".me" => "application/x-troff-me",
  ".ms" => "application/x-troff-ms",
  ".ustar" => "application/x-ustar",
  ".src" => "application/x-wais-source",
  ".wz" => "application/x-wingz",
  ".crt" => "application/x-x509-ca-cert",
  ".xcf" => "application/x-xcf",
  ".fig" => "application/x-xfig",
  ".xpi" => "application/x-xpinstall",
  ".xz" => "application/x-xz",
  ".amr" => "audio/amr",
  ".awb" => "audio/amr-wb",
  ".axa" => "audio/annodex",
  ".au" => "audio/basic",
  ".snd" => "audio/basic",
  ".csd" => "audio/csound",
  ".orc" => "audio/csound",
  ".sco" => "audio/csound",
  ".flac" => "audio/flac",
  ".kar" => "audio/midi",
  ".mid" => "audio/midi",
  ".midi" => "audio/midi",
  ".m4a" => "audio/mpeg",
  ".mp2" => "audio/mpeg",
  ".mp3" => "audio/mpeg",
  ".mpega" => "audio/mpeg",
  ".mpga" => "audio/mpeg",
  ".m3u" => "audio/mpegurl",
  ".oga" => "audio/ogg",
  ".ogg" => "audio/ogg",
  ".opus" => "audio/ogg",
  ".spx" => "audio/ogg",
  ".sid" => "audio/prs.sid",
  ".aif" => "audio/x-aiff",
  ".aifc" => "audio/x-aiff",
  ".aiff" => "audio/x-aiff",
  ".gsm" => "audio/x-gsm",
  ".wax" => "audio/x-ms-wax",
  ".wma" => "audio/x-ms-wma",
  ".ra" => "audio/x-realaudio",
  ".ram" => "audio/x-realaudio",
  ".rm" => "audio/x-realaudio",
  ".pls" => "audio/x-scpls",
  ".sd2" => "audio/x-sd2",
  ".wav" => "audio/x-wav",
  ".alc" => "chemical/x-alchemy",
  ".cac" => "chemical/x-cache",
  ".cache" => "chemical/x-cache",
  ".csf" => "chemical/x-cache-csf",
  ".cascii" => "chemical/x-cactvs-binary",
  ".cbin" => "chemical/x-cactvs-binary",
  ".ctab" => "chemical/x-cactvs-binary",
  ".cdx" => "chemical/x-cdx",
  ".cer" => "chemical/x-cerius",
  ".c3d" => "chemical/x-chem3d",
  ".chm" => "chemical/x-chemdraw",
  ".cif" => "chemical/x-cif",
  ".cmdf" => "chemical/x-cmdf",
  ".cml" => "chemical/x-cml",
  ".cpa" => "chemical/x-compass",
  ".bsd" => "chemical/x-crossfire",
  ".csm" => "chemical/x-csml",
  ".csml" => "chemical/x-csml",
  ".ctx" => "chemical/x-ctx",
  ".cef" => "chemical/x-cxf",
  ".cxf" => "chemical/x-cxf",
  ".emb" => "chemical/x-embl-dl-nucleotide",
  ".embl" => "chemical/x-embl-dl-nucleotide",
  ".spc" => "chemical/x-galactic-spc",
  ".gam" => "chemical/x-gamess-input",
  ".gamin" => "chemical/x-gamess-input",
  ".inp" => "chemical/x-gamess-input",
  ".fch" => "chemical/x-gaussian-checkpoint",
  ".fchk" => "chemical/x-gaussian-checkpoint",
  ".cub" => "chemical/x-gaussian-cube",
  ".gau" => "chemical/x-gaussian-input",
  ".gjc" => "chemical/x-gaussian-input",
  ".gjf" => "chemical/x-gaussian-input",
  ".gal" => "chemical/x-gaussian-log",
  ".gcg" => "chemical/x-gcg8-sequence",
  ".gen" => "chemical/x-genbank",
  ".hin" => "chemical/x-hin",
  ".ist" => "chemical/x-isostar",
  ".istr" => "chemical/x-isostar",
  ".dx" => "chemical/x-jcamp-dx",
  ".jdx" => "chemical/x-jcamp-dx",
  ".kin" => "chemical/x-kinemage",
  ".mcm" => "chemical/x-macmolecule",
  ".mmd" => "chemical/x-macromodel-input",
  ".mmod" => "chemical/x-macromodel-input",
  ".mol" => "chemical/x-mdl-molfile",
  ".rd" => "chemical/x-mdl-rdfile",
  ".rxn" => "chemical/x-mdl-rxnfile",
  ".sd" => "chemical/x-mdl-sdfile",
  ".tgf" => "chemical/x-mdl-tgf",
  ".mcif" => "chemical/x-mmcif",
  ".mol2" => "chemical/x-mol2",
  ".b" => "chemical/x-molconn-Z",
  ".gpt" => "chemical/x-mopac-graph",
  ".mop" => "chemical/x-mopac-input",
  ".mopcrt" => "chemical/x-mopac-input",
  ".mpc" => "chemical/x-mopac-input",
  ".zmt" => "chemical/x-mopac-input",
  ".moo" => "chemical/x-mopac-out",
  ".mvb" => "chemical/x-mopac-vib",
  ".prt" => "chemical/x-ncbi-asn1-ascii",
  ".aso" => "chemical/x-ncbi-asn1-binary",
  ".val" => "chemical/x-ncbi-asn1-binary",
  ".pdb" => "chemical/x-pdb",
  ".ros" => "chemical/x-rosdal",
  ".sw" => "chemical/x-swissprot",
  ".vms" => "chemical/x-vamas-iso14976",
  ".vmd" => "chemical/x-vmd",
  ".xtel" => "chemical/x-xtel",
  ".xyz" => "chemical/x-xyz",
  ".otf" => "font/ttf",
  ".ttf" => "font/ttf",
  ".woff" => "font/woff",
  ".gif" => "image/gif",
  ".ief" => "image/ief",
  ".jp2" => "image/jp2",
  ".jpg2" => "image/jp2",
  ".jpe" => "image/jpeg",
  ".jpeg" => "image/jpeg",
  ".jpg" => "image/jpeg",
  ".jpm" => "image/jpm",
  ".jpf" => "image/jpx",
  ".jpx" => "image/jpx",
  ".pcx" => "image/pcx",
  ".png" => "image/png",
  ".svg" => "image/svg+xml",
  ".svgz" => "image/svg+xml",
  ".tif" => "image/tiff",
  ".tiff" => "image/tiff",
  ".djv" => "image/vnd.djvu",
  ".djvu" => "image/vnd.djvu",
  ".ico" => "image/vnd.microsoft.icon",
  ".wbmp" => "image/vnd.wap.wbmp",
  ".cr2" => "image/x-canon-cr2",
  ".crw" => "image/x-canon-crw",
  ".ras" => "image/x-cmu-raster",
  ".cdr" => "image/x-coreldraw",
  ".pat" => "image/x-coreldrawpattern",
  ".cdt" => "image/x-coreldrawtemplate",
  ".erf" => "image/x-epson-erf",
  ".art" => "image/x-jg",
  ".jng" => "image/x-jng",
  ".bmp" => "image/x-ms-bmp",
  ".nef" => "image/x-nikon-nef",
  ".orf" => "image/x-olympus-orf",
  ".psd" => "image/x-photoshop",
  ".pnm" => "image/x-portable-anymap",
  ".pbm" => "image/x-portable-bitmap",
  ".pgm" => "image/x-portable-graymap",
  ".ppm" => "image/x-portable-pixmap",
  ".rgb" => "image/x-rgb",
  ".xbm" => "image/x-xbitmap",
  ".xpm" => "image/x-xpixmap",
  ".xwd" => "image/x-xwindowdump",
  ".eml" => "message/rfc822",
  ".iges" => "model/iges",
  ".igs" => "model/iges",
  ".mesh" => "model/mesh",
  ".msh" => "model/mesh",
  ".silo" => "model/mesh",
  ".vrml" => "model/vrml",
  ".wrl" => "model/vrml",
  ".x3db" => "model/x3d+binary",
  ".x3dv" => "model/x3d+vrml",
  ".x3d" => "model/x3d+xml",
  ".appcache" => "text/cache-manifest; charset=utf-8",
  ".ics" => "text/calendar; charset=utf-8",
  ".icz" => "text/calendar; charset=utf-8",
  ".css" => "text/css; charset=utf-8",
  ".csv" => "text/csv; charset=utf-8",
  ".323" => "text/h323; charset=utf-8",
  ".htm" => "text/html",
  ".html" => "text/html",
  ".shtml" => "text/html",
  ".uls" => "text/iuls; charset=utf-8",
  ".markdown" => "text/markdown; charset=utf-8",
  ".md" => "text/markdown; charset=utf-8",
  ".mml" => "text/mathml; charset=utf-8",
  ".asc" => "text/plain; charset=utf-8",
  ".brf" => "text/plain; charset=utf-8",
  ".conf" => "text/plain; charset=utf-8",
  ".log" => "text/plain; charset=utf-8",
  ".pot" => "text/plain; charset=utf-8",
  ".spec" => "text/plain; charset=utf-8",
  ".srt" => "text/plain; charset=utf-8",
  ".text" => "text/plain; charset=utf-8",
  ".txt" => "text/plain; charset=utf-8",
  ".rtx" => "text/richtext; charset=utf-8",
  ".sct" => "text/scriptlet; charset=utf-8",
  ".wsc" => "text/scriptlet; charset=utf-8",
  ".tsv" => "text/tab-separated-values; charset=utf-8",
  ".tm" => "text/texmacs; charset=utf-8",
  ".ttl" => "text/turtle; charset=utf-8",
  ".vcard" => "text/vcard; charset=utf-8",
  ".vcf" => "text/vcard; charset=utf-8",
  ".jad" => "text/vnd.sun.j2me.app-descriptor; charset=utf-8",
  ".wml" => "text/vnd.wap.wml; charset=utf-8",
  ".wmls" => "text/vnd.wap.wmlscript; charset=utf-8",
  ".bib" => "text/x-bibtex; charset=utf-8",
  ".boo" => "text/x-boo; charset=utf-8",
  ".h++" => "text/x-c++hdr; charset=utf-8",
  ".hh" => "text/x-c++hdr; charset=utf-8",
  ".hpp" => "text/x-c++hdr; charset=utf-8",
  ".hxx" => "text/x-c++hdr; charset=utf-8",
  ".c++" => "text/x-c++src; charset=utf-8",
  ".cc" => "text/x-c++src; charset=utf-8",
  ".cpp" => "text/x-c++src; charset=utf-8",
  ".cxx" => "text/x-c++src; charset=utf-8",
  ".h" => "text/x-chdr; charset=utf-8",
  ".htc" => "text/x-component; charset=utf-8",
  ".csh" => "text/x-csh; charset=utf-8",
  ".c" => "text/x-csrc; charset=utf-8",
  ".diff" => "text/x-diff; charset=utf-8",
  ".patch" => "text/x-diff; charset=utf-8",
  ".d" => "text/x-dsrc; charset=utf-8",
  ".hs" => "text/x-haskell; charset=utf-8",
  ".java" => "text/x-java; charset=utf-8",
  ".ly" => "text/x-lilypond; charset=utf-8",
  ".lhs" => "text/x-literate-haskell; charset=utf-8",
  ".moc" => "text/x-moc; charset=utf-8",
  ".p" => "text/x-pascal; charset=utf-8",
  ".pas" => "text/x-pascal; charset=utf-8",
  ".gcd" => "text/x-pcs-gcd; charset=utf-8",
  ".pl" => "text/x-perl; charset=utf-8",
  ".pm" => "text/x-perl; charset=utf-8",
  ".py" => "text/x-python; charset=utf-8",
  ".scala" => "text/x-scala; charset=utf-8",
  ".etx" => "text/x-setext; charset=utf-8",
  ".sfv" => "text/x-sfv; charset=utf-8",
  ".sh" => "text/x-sh; charset=utf-8",
  ".tcl" => "text/x-tcl; charset=utf-8",
  ".tk" => "text/x-tcl; charset=utf-8",
  ".cls" => "text/x-tex; charset=utf-8",
  ".ltx" => "text/x-tex; charset=utf-8",
  ".sty" => "text/x-tex; charset=utf-8",
  ".tex" => "text/x-tex; charset=utf-8",
  ".vcs" => "text/x-vcalendar; charset=utf-8",
  ".3gp" => "video/3gpp",
  ".ts" => "video/MP2T",
  ".axv" => "video/annodex",
  ".dl" => "video/dl",
  ".dif" => "video/dv",
  ".dv" => "video/dv",
  ".fli" => "video/fli",
  ".gl" => "video/gl",
  ".mp4" => "video/mp4",
  ".mpe" => "video/mpeg",
  ".mpeg" => "video/mpeg",
  ".mpg" => "video/mpeg",
  ".ogv" => "video/ogg",
  ".mov" => "video/quicktime",
  ".qt" => "video/quicktime",
  ".webm" => "video/webm",
  ".mxu" => "video/vnd.mpegurl",
  ".flv" => "video/x-flv",
  ".lsf" => "video/x-la-asf",
  ".lsx" => "video/x-la-asf",
  ".mkv" => "video/x-matroska",
  ".mpv" => "video/x-matroska",
  ".mng" => "video/x-mng",
  ".asf" => "video/x-ms-asf",
  ".asx" => "video/x-ms-asf",
  ".wm" => "video/x-ms-wm",
  ".wmv" => "video/x-ms-wmv",
  ".wmx" => "video/x-ms-wmx",
  ".wvx" => "video/x-ms-wvx",
  ".avi" => "video/x-msvideo",
  ".movie" => "video/x-sgi-movie",
  ".ice" => "x-conference/x-cooltalk",
  ".sisx" => "x-epoc/x-sisx-app",
  ".vrm" => "x-world/x-vrml",
  "README" => "text/plain; charset=utf-8",
  "Makefile" => "text/x-makefile; charset=utf-8",
)

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

    NAME = "lighttpd-plain"
    QUEUE = "webgrid-lighttpd"

    def check(self):
        # Check for a .lighttpd.conf file or a public_html
        public_html_path = self.tool.get_homedir_subpath("public_html")
        lighttpd_conf_path = self.tool.get_homedir_subpath(".lighttpd.conf")
        if not (
            os.path.exists(public_html_path)
            or os.path.exists(lighttpd_conf_path)
        ):
            raise WebService.InvalidWebServiceException(
                "Could not find a public_html folder or a .lighttpd.conf "
                "file in your tool home."
            )

    def build_config(self, port, config_template=BASIC_CONFIG_TEMPLATE):
        config = config_template.format(
            toolname=self.tool.name,
            username=self.tool.username,
            groupname=self.tool.username,
            home=self.tool.home,
            port=port,
        )
        try:
            with open(self.tool.get_homedir_subpath(".lighttpd.conf")) as f:
                config += f.read()
        except IOError:
            pass  # No customized file, not a big deal
        return config

    def run(self, port):
        config = self.build_config(port)
        config_path = os.path.join("/var/run/lighttpd/", self.tool.name)
        with open(config_path, "w") as f:
            f.write(config)

        os.execv(
            "/usr/sbin/lighttpd",
            ["/usr/sbin/lighttpd", "-f", config_path, "-D"],
        )


class LighttpdWebService(LighttpdPlainWebService):
    """
    A Lighttpd Webserver with a default PHP setup
    """

    NAME = "lighttpd"
    QUEUE = "webgrid-lighttpd"

    def build_config(
        self,
        port,
        config_template=BASIC_CONFIG_TEMPLATE + ENABLE_PHP_CONFIG_TEMPLATE,
    ):
        return super(LighttpdWebService, self).build_config(
            port, config_template
        )
