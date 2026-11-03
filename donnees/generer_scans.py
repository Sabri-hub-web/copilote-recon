"""Génère les 20 scans du benchmark (brique 9) ET leurs bonnes réponses.

  - série facile    : scan_01 à scan_10  -> bench/taches.json
  - série difficile : scan_11 à scan_20  -> bench/taches_difficiles.json

Pourquoi des scans générés ? Pour la brique 9, il faut des tâches dont on
CONNAÎT la réponse. Ici, la vérité (les ports ouverts) est écrite à la main
dans MACHINES ci-dessous, indépendamment du code qui lit les scans.

Chaque scan contient des pièges : ports "closed", "filtered", "open|filtered".
Un modèle qui lit mal le XML les comptera comme ouverts.

    python donnees/generer_scans.py
"""
import json
from pathlib import Path

DOSSIER = Path(__file__).resolve().parent
SORTIE_XML = DOSSIER / "scans_bench"
SORTIE_TACHES = DOSSIER.parent / "bench" / "taches.json"

# (port, protocole, état, service, produit, version)
MACHINES = {
    "scan_01": ("172.17.0.2", [
        (22, "tcp", "open", "ssh", "OpenSSH", "8.9p1 Ubuntu 3ubuntu0.6"),
        (80, "tcp", "open", "http", "Apache httpd", "2.4.52"),
        (443, "tcp", "closed", "https", "", ""),
    ]),
    "scan_02": ("172.17.0.3", [
        (22, "tcp", "filtered", "ssh", "", ""),
        (80, "tcp", "open", "http", "nginx", "1.18.0"),
        (443, "tcp", "open", "https", "nginx", "1.18.0"),
        (3306, "tcp", "closed", "mysql", "", ""),
        (8080, "tcp", "open", "http-proxy", "Apache Tomcat", "9.0.30"),
    ]),
    "scan_03": ("172.17.0.4", [
        (80, "tcp", "filtered", "http", "", ""),
        (135, "tcp", "open", "msrpc", "Microsoft Windows RPC", ""),
        (139, "tcp", "open", "netbios-ssn", "Microsoft Windows netbios-ssn", ""),
        (445, "tcp", "open", "microsoft-ds", "Microsoft Windows Server 2016", ""),
        (3389, "tcp", "open", "ms-wbt-server", "Microsoft Terminal Services", ""),
    ]),
    "scan_04": ("172.17.0.5", [
        (22, "tcp", "open", "ssh", "OpenSSH", "7.4"),
        (3306, "tcp", "open", "mysql", "MySQL", "5.7.33"),
        (5432, "tcp", "open", "postgresql", "PostgreSQL DB", "9.6"),
        (6379, "tcp", "open", "redis", "Redis key-value store", "4.0.9"),
        (27017, "tcp", "closed", "mongodb", "", ""),
    ]),
    "scan_05": ("172.17.0.6", [
        (21, "tcp", "open", "ftp", "vsftpd", "2.3.4"),
        (22, "tcp", "open", "ssh", "OpenSSH", "4.7p1 Debian 8ubuntu1"),
        (23, "tcp", "closed", "telnet", "", ""),
        (25, "tcp", "filtered", "smtp", "", ""),
        (80, "tcp", "open", "http", "Apache httpd", "2.2.8"),
    ]),
    "scan_06": ("172.17.0.7", [  # gros scan type Metasploitable : 20 ports ouverts
        (21, "tcp", "open", "ftp", "vsftpd", "2.3.4"),
        (22, "tcp", "open", "ssh", "OpenSSH", "4.7p1"),
        (23, "tcp", "open", "telnet", "Linux telnetd", ""),
        (25, "tcp", "open", "smtp", "Postfix smtpd", ""),
        (53, "tcp", "open", "domain", "ISC BIND", "9.4.2"),
        (80, "tcp", "open", "http", "Apache httpd", "2.2.8"),
        (111, "tcp", "open", "rpcbind", "", "2"),
        (139, "tcp", "open", "netbios-ssn", "Samba smbd", "3.X - 4.X"),
        (445, "tcp", "open", "netbios-ssn", "Samba smbd", "3.0.20-Debian"),
        (512, "tcp", "open", "exec", "netkit-rsh rexecd", ""),
        (513, "tcp", "open", "login", "", ""),
        (514, "tcp", "open", "tcpwrapped", "", ""),
        (1099, "tcp", "open", "java-rmi", "GNU Classpath grmiregistry", ""),
        (1524, "tcp", "open", "bindshell", "Metasploitable root shell", ""),
        (2049, "tcp", "open", "nfs", "", "2-4"),
        (2121, "tcp", "filtered", "ccproxy-ftp", "", ""),
        (3306, "tcp", "open", "mysql", "MySQL", "5.0.51a-3ubuntu5"),
        (5432, "tcp", "open", "postgresql", "PostgreSQL DB", "8.3.0 - 8.3.7"),
        (5900, "tcp", "open", "vnc", "VNC", "protocol 3.3"),
        (6000, "tcp", "open", "X11", "", ""),
        (6667, "tcp", "open", "irc", "UnrealIRCd", ""),
        (8009, "tcp", "closed", "ajp13", "", ""),
        (8180, "tcp", "open", "http", "Apache Tomcat/Coyote JSP engine", "1.1"),
    ]),
    "scan_07": ("172.17.0.8", [  # un seul port ouvert, beaucoup de leurres
        (21, "tcp", "closed", "ftp", "", ""),
        (22, "tcp", "closed", "ssh", "", ""),
        (25, "tcp", "closed", "smtp", "", ""),
        (80, "tcp", "closed", "http", "", ""),
        (443, "tcp", "open", "https", "nginx", "1.24.0"),
        (3389, "tcp", "filtered", "ms-wbt-server", "", ""),
    ]),
    "scan_08": ("172.17.0.9", [  # UDP + état ambigu "open|filtered"
        (22, "tcp", "open", "ssh", "OpenSSH", "9.2p1"),
        (53, "udp", "open", "domain", "dnsmasq", "2.89"),
        (123, "udp", "open", "ntp", "NTP", "v4"),
        (161, "udp", "open|filtered", "snmp", "", ""),
        (500, "udp", "open|filtered", "isakmp", "", ""),
    ]),
    "scan_09": ("172.17.0.10", [  # ports non standards : SSH n'est PAS sur 22
        (22, "tcp", "closed", "ssh", "", ""),
        (2222, "tcp", "open", "ssh", "OpenSSH", "8.4p1"),
        (8443, "tcp", "open", "https-alt", "Jetty", "9.4.z"),
        (9200, "tcp", "open", "http", "Elasticsearch REST API", "7.10.2"),
        (27017, "tcp", "open", "mongodb", "MongoDB", "4.4.6"),
    ]),
    "scan_10": ("172.17.0.11", [  # OWASP Juice Shop dans Docker
        (22, "tcp", "open", "ssh", "OpenSSH", "8.9p1"),
        (80, "tcp", "closed", "http", "", ""),
        (3000, "tcp", "open", "http", "Node.js Express framework", ""),
        (8080, "tcp", "filtered", "http-proxy", "", ""),
    ]),
}


# ---------------------------------------------------------------------------
# SÉRIE DIFFICILE (scan_11 à scan_20)
# Ajoutée après le premier benchmark : sur les 10 premiers scans, Qwen seul
# avait déjà 100 % de réponses justes (effet plafond). Ici : 30 à 45 ports
# ouverts, beaucoup de leurres, et des numéros présents en TCP "closed" ET en
# UDP "open" (ou l'inverse). La vérité reste écrite par ce script, pas par lire_scan.
# ---------------------------------------------------------------------------
CATALOGUE = [  # (port, service, produit, version)
    (21, "ftp", "vsftpd", "3.0.3"), (22, "ssh", "OpenSSH", "8.2p1"), (23, "telnet", "Linux telnetd", ""),
    (25, "smtp", "Postfix smtpd", ""), (53, "domain", "ISC BIND", "9.16.1"), (69, "tftp", "", ""),
    (80, "http", "Apache httpd", "2.4.41"), (81, "http", "nginx", "1.14.0"), (88, "kerberos-sec", "Microsoft Windows Kerberos", ""),
    (110, "pop3", "Dovecot pop3d", ""), (111, "rpcbind", "", "2-4"), (119, "nntp", "INN", ""),
    (123, "ntp", "NTP", "v4"), (135, "msrpc", "Microsoft Windows RPC", ""), (137, "netbios-ns", "", ""),
    (139, "netbios-ssn", "Samba smbd", "4.6.2"), (143, "imap", "Dovecot imapd", ""), (161, "snmp", "net-snmp", "5.7.3"),
    (179, "bgp", "", ""), (389, "ldap", "OpenLDAP", "2.4.57"), (443, "https", "Apache httpd", "2.4.41"),
    (445, "microsoft-ds", "Samba smbd", "4.6.2"), (465, "smtps", "Postfix smtpd", ""), (500, "isakmp", "", ""),
    (514, "syslog", "", ""), (515, "printer", "", ""), (548, "afp", "Netatalk", "3.1.12"),
    (554, "rtsp", "", ""), (587, "submission", "Postfix smtpd", ""), (631, "ipp", "CUPS", "2.3"),
    (636, "ldapssl", "OpenLDAP", ""), (873, "rsync", "", "protocol 31"), (993, "imaps", "Dovecot imapd", ""),
    (995, "pop3s", "Dovecot pop3d", ""), (1080, "socks5", "", ""), (1194, "openvpn", "OpenVPN", ""),
    (1433, "ms-sql-s", "Microsoft SQL Server 2017", "14.00.1000"), (1521, "oracle-tns", "Oracle TNS listener", "11.2.0.2.0"),
    (1723, "pptp", "", ""), (1883, "mqtt", "Mosquitto", "1.6.9"), (2049, "nfs", "", "3-4"),
    (2375, "docker", "Docker", "20.10.7"), (2379, "etcd-client", "etcd", "3.4.13"), (3000, "http", "Grafana", "7.5.2"),
    (3128, "http-proxy", "Squid http proxy", "4.10"), (3306, "mysql", "MySQL", "5.7.33"), (3389, "ms-wbt-server", "xrdp", ""),
    (3690, "svn", "Subversion", ""), (4369, "epmd", "Erlang Port Mapper Daemon", ""), (5000, "http", "Werkzeug httpd", "1.0.1"),
    (5060, "sip", "Asterisk", "16.2.1"), (5432, "postgresql", "PostgreSQL DB", "12.5"), (5601, "http", "Kibana", "7.10.2"),
    (5672, "amqp", "RabbitMQ", "3.8.9"), (5900, "vnc", "VNC", "protocol 3.8"), (5985, "http", "Microsoft HTTPAPI httpd", "2.0"),
    (6379, "redis", "Redis key-value store", "6.0.9"), (6443, "https", "Kubernetes API", ""), (7001, "http", "Oracle WebLogic", "12.2.1.3"),
    (8000, "http", "SimpleHTTPServer", "0.6"), (8008, "http", "", ""), (8080, "http-proxy", "Jenkins", "2.263.1"),
    (8081, "http", "Nexus Repository Manager", "3.29"), (8086, "http", "InfluxDB", "1.8.3"), (8443, "https-alt", "", ""),
    (8888, "http", "Jupyter Notebook", "6.1.5"), (9000, "http", "SonarQube", "8.6"), (9090, "http", "Prometheus", "2.24.0"),
    (9092, "kafka", "Apache Kafka", ""), (9100, "jetdirect", "", ""), (9200, "http", "Elasticsearch REST API", "7.10.2"),
    (9418, "git", "", ""), (10000, "http", "MiniServ (Webmin httpd)", "1.962"), (11211, "memcache", "Memcached", "1.6.9"),
    (15672, "http", "RabbitMQ management", ""), (27017, "mongodb", "MongoDB", "4.4.3"), (50000, "http", "Jenkins agent", ""),
]
PORTS_UDP = [53, 69, 123, 137, 161, 500, 514, 1194, 1900, 5060, 5353]


def machines_difficiles():
    import random
    machines = {}
    for i in range(11, 21):
        hasard = random.Random(i)          # graine fixe : toujours les mêmes scans
        melange = hasard.sample(CATALOGUE, len(CATALOGUE))
        n_ouverts = hasard.randint(30, 45)
        ports = []
        for port, service, produit, version in melange[:n_ouverts]:
            ports.append((port, "tcp", "open", service, produit, version))
        for port, service, _, _ in melange[n_ouverts:n_ouverts + 25]:   # leurres TCP
            ports.append((port, "tcp", hasard.choice(["closed", "filtered"]), service, "", ""))
        for port in hasard.sample(PORTS_UDP, 5):                         # UDP : 2 ouverts, 3 ambigus
            etat = "open" if len([p for p in ports if p[1] == "udp" and p[2] == "open"]) < 2 \
                else "open|filtered"
            if not any(p[0] == port and p[1] == "tcp" for p in ports):  # même numéro en TCP fermé
                ports.append((port, "tcp", "closed", "inconnu", "", ""))
            ports.append((port, "udp", etat, "inconnu", "", ""))
        ports.sort(key=lambda p: (p[1], p[0]))   # nmap trie par protocole puis par port
        machines[f"scan_{i}"] = (f"172.18.0.{i}", ports)
    return machines


def xml_du_scan(ip, ports):
    """Écrit un XML au même format que 'nmap -sV -oX'."""
    lignes = []
    for port, proto, etat, service, produit, version in ports:
        attributs = f'name="{service}"'
        if produit:
            attributs += f' product="{produit}"'
        if version:
            attributs += f' version="{version}"'
        raison = "syn-ack" if etat == "open" else ("reset" if etat == "closed" else "no-response")
        lignes.append(
            f'<port protocol="{proto}" portid="{port}">'
            f'<state state="{etat}" reason="{raison}" reason_ttl="64"/>'
            f'<service {attributs} method="probed" conf="10"/></port>')
    ports_xml = "\n".join(lignes)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE nmaprun>
<nmaprun scanner="nmap" args="nmap -sV -sU -sS -oX scan.xml {ip}" start="1762100000" version="7.94" xmloutputversion="1.05">
<scaninfo type="syn" protocol="tcp" numservices="1000" services="1-1000"/>
<host starttime="1762100000" endtime="1762100042"><status state="up" reason="arp-response" reason_ttl="0"/>
<address addr="{ip}" addrtype="ipv4"/>
<hostnames></hostnames>
<ports><extraports state="closed" count="{1000 - len(ports)}"><extrareasons reason="reset" count="{1000 - len(ports)}"/></extraports>
{ports_xml}
</ports>
</host>
<runstats><finished time="1762100042" elapsed="42.00" exit="success"/><hosts up="1" down="0" total="1"/></runstats>
</nmaprun>
"""


def ecrire(machines, fichier_taches):
    SORTIE_XML.mkdir(parents=True, exist_ok=True)
    taches = []
    for nom, (ip, ports) in machines.items():
        (SORTIE_XML / f"{nom}.xml").write_text(xml_du_scan(ip, ports), encoding="utf-8")
        taches.append({
            "id": nom,
            "fichier": f"donnees/scans_bench/{nom}.xml",
            # LA BONNE RÉPONSE : uniquement les ports dont l'état est exactement "open"
            # (set : un même numéro ouvert en TCP et en UDP ne compte qu'une fois)
            "ports_ouverts": sorted({p[0] for p in ports if p[2] == "open"}),
        })
    fichier_taches.parent.mkdir(exist_ok=True)
    fichier_taches.write_text(json.dumps(taches, indent=2), encoding="utf-8")
    print(f"{len(taches)} scans écrits dans {SORTIE_XML} et réponses dans {fichier_taches}")


def main():
    ecrire(MACHINES, SORTIE_TACHES)                                   # série facile
    ecrire(machines_difficiles(), SORTIE_TACHES.with_name("taches_difficiles.json"))


if __name__ == "__main__":
    main()
