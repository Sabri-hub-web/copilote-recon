"""Génère les 10 scans du benchmark (brique 9) ET leurs bonnes réponses.

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


def main():
    SORTIE_XML.mkdir(parents=True, exist_ok=True)
    taches = []
    for nom, (ip, ports) in MACHINES.items():
        (SORTIE_XML / f"{nom}.xml").write_text(xml_du_scan(ip, ports), encoding="utf-8")
        taches.append({
            "id": nom,
            "fichier": f"donnees/scans_bench/{nom}.xml",
            # LA BONNE RÉPONSE : uniquement les ports dont l'état est exactement "open"
            "ports_ouverts": sorted(p[0] for p in ports if p[2] == "open"),
        })
    SORTIE_TACHES.parent.mkdir(exist_ok=True)
    SORTIE_TACHES.write_text(json.dumps(taches, indent=2), encoding="utf-8")
    print(f"{len(taches)} scans écrits dans {SORTIE_XML} et réponses dans {SORTIE_TACHES}")


if __name__ == "__main__":
    main()
