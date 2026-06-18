# Automatisation du Déploiement d'Infrastructure OPCP OpenStack OVH

Système d'automatisation pour le déploiement et la gestion d'infrastructure cloud privé OVH OpenStack avec trois approches de déploiement distinctes : Terraform, OpenStack SDK et Ansible.

## Aperçu

Ce projet fournit plusieurs solutions pour déployer et gérer l'infrastructure OVH OpenStack :

1. **Solution Terraform** : Infrastructure as Code avec configuration déclarative
2. **Solution OpenStack SDK** : Déploiement basé sur Python de manière programmatique
3. **Solution Ansible** : Gestion de configuration avec playbooks idempotents

Toutes les solutions partagent un format de configuration commun et prennent en charge les mêmes types de ressources :
- Instances de calcul
- Réseaux et sous-réseaux
- Volumes de stockage
- Groupes de sécurité
- IP flottantes

## Structure du Projet

```
.
├── config/                 # Gestion partagée de la configuration
│   ├── config_manager.py   # Chargeur et validateur de configuration
│   └── models.py           # Modèles de données
├── utils/                  # Modules utilitaires
│   └── logger.py           # Infrastructure de journalisation
├── terraform/              # Solution de déploiement Terraform
├── openstack_sdk/          # Solution de déploiement OpenStack SDK
├── ansible/                # Solution de déploiement Ansible
├── examples/               # Fichiers de configuration d'exemple
│   ├── config.yaml         # Exemple complet (YAML)
│   ├── config.json         # Exemple complet (JSON)
│   └── minimal-config.yaml # Exemple minimal
├── requirements.txt        # Dépendances Python
└── requirements-dev.txt    # Dépendances de développement
```

## Démarrage Rapide

### Prérequis

- Python >= 3.8
- Compte valide OVH OpenStack avec identifiants
- Clé SSH enregistrée dans OVH OpenStack

### Installation

1. Clonez le dépôt :
```bash
git clone <url-du-dépôt>
cd ovh-openstack-deployment
```

2. Installez les dépendances Python :
```bash
pip install -r requirements.txt
```

3. Configurez les variables d'environnement pour l'authentification :
   
   **Pour l'authentification traditionnelle nom d'utilisateur/mot de passe :**
   ```bash
   export OS_AUTH_URL=https://auth.cloud.ovh.net/v3
   export OS_USERNAME=votre-nom-d-utilisateur
   export OS_PASSWORD=votre-mot-de-passe
   export OS_TENANT_NAME=votre-nom-de-projet
   export OS_REGION_NAME=GRA7
   ```

   **Pour les identifiants d'application :**
   ```bash
   export OS_AUTH_TYPE=v3applicationcredential
   export OS_AUTH_URL=https://keystone.demo.bmp.ovhgoldorack.ovh/v3
   export OS_IDENTITY_API_VERSION=3
   export OS_REGION_NAME="demo"
   export OS_INTERFACE=public
   export OS_APPLICATION_CREDENTIAL_ID=votre_id
   export OS_APPLICATION_CREDENTIAL_SECRET=votre_secret
   ```

   Ou utilisez le script pratique :
   ```bash
   source examples/set_app_cred_env.sh
   ```

4. Installation de Shai genAI pour vous aider à coder et déboguer :

```bash
# Installez la dernière version avec la commande suivante :
curl -fsSL https://raw.githubusercontent.com/ovh/shai/main/install.sh | sh

# Le binaire shai sera installé dans $HOME/.local/bin
# Configurez ensuite l'authentification pour Shai
shai auth

# Pour l'aide au codage, utilisez ● ovhcloud - Qwen3-Coder-30B-A3B-Instruct
```

### Configuration

Créez un fichier de configuration basé sur les exemples :

```bash
cp examples/minimal-config.yaml ma-config.yaml
# Éditez ma-config.yaml avec vos paramètres
```

### Validation de la Configuration

```python
from config import ConfigurationManager

manager = ConfigurationManager()
config = manager.load_config('examples/minimal-config.yaml')
validation = manager.validate_config(config)

if validation.is_valid:
    print("La configuration est valide !")
else:
    print("Erreurs de validation :")
    for error in validation.errors:
        print(f"  - {error}")
```

### Exécution des Exemples

Pour exécuter les exemples avec des identifiants d'application :

1. Configurez vos variables d'environnement comme indiqué ci-dessus
2. Exécutez l'exemple des identifiants d'application :
```bash
python examples/app_cred_example.py
```

Ou exécutez des exemples individuels :
```bash
python examples/auth_example.py
python examples/compute_example.py
python examples/network_example.py
python examples/security_group_example.py
python examples/volume_example.py
```

Vous pouvez également exécuter le script de démonstration pour voir comment fonctionne la gestion de configuration :
```bash
python demo.py
```

Les exemples montrent à la fois l'authentification directe et l'utilisation du ConnectionManager qui gère le renouvellement automatique des jetons et le support des proxies.

## Format de Configuration

Le système utilise un format de configuration unifié (YAML ou JSON) pour toutes les solutions de déploiement :

### Authentification Traditionnelle
```yaml
# Authentification
auth_url: "https://auth.cloud.ovh.net/v3"
username: "${OS_USERNAME}"
password: "${OS_PASSWORD}"
tenant_name: "${OS_TENANT_NAME}"
region: "GRA7"
project_name: "mon-projet"

# Réseaux
networks:
  - name: "réseau-prive"
    subnets:
      - name: "sous-réseau-prive"
        cidr: "192.168.1.0/24"

# Groupes de Sécurité
security_groups:
  - name: "sg-web"
    description: "Groupe de sécurité du serveur web"
    rules:
      - direction: "ingress"
        protocol: "tcp"
        port_range_min: 22
        port_range_max: 22
        remote_ip_prefix: "0.0.0.0/0"

# Instances
instances:
  - name: "serveur-web-1"
    flavor: "scale-1"
    image: "Debian 12 LVM OPCP"
    key_name: "opcp-openstack-automation-ssh-key"
    network_ids: ["réseau-prive"]
    security_groups: ["sg-web"]

# Volumes
volumes:
  - name: "volume-data-1"
    size: 100
    volume_type: "classic"
    attach_to: "serveur-web-1"
```

### Authentification avec Identifiants d'Application
```yaml
# Authentification pour les identifiants d'application
auth_url: "${OS_AUTH_URL}"
auth_type: "${OS_AUTH_TYPE}"
region: "${OS_REGION_NAME}"
project_name: "${OS_TENANT_NAME}"
application_credential_id: "${OS_APPLICATION_CREDENTIAL_ID}"
application_credential_secret: "${OS_APPLICATION_CREDENTIAL_SECRET}"

# Réseaux
networks:
  - name: "réseau-prive"
    subnets:
      - name: "sous-réseau-prive"
        cidr: "192.168.1.0/24"

# Groupes de Sécurité
security_groups:
  - name: "sg-web"
    description: "Groupe de sécurité du serveur web"
    rules:
      - direction: "ingress"
        protocol: "tcp"
        port_range_min: 22
        port_range_max: 22
        remote_ip_prefix: "0.0.0.0/0"

# Instances
instances:
  - name: "serveur-web-1"
    flavor: "scale-1"
    image: "Debian 12 LVM OPCP"
    key_name: "opcp-openstack-automation-ssh-key"
    network_ids: ["réseau-prive"]
    security_groups: ["sg-web"]

# Volumes
volumes:
  - name: "volume-data-1"
    size: 100
    volume_type: "classic"
    attach_to: "serveur-web-1"
```

Voir `examples/README.md` pour une référence complète de la configuration.

## Solutions de Déploiement

### Solution Terraform

Infrastructure as Code avec gestion d'état et résolution des dépendances.

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

Voir `terraform/README.md` pour les détails.

### Solution OpenStack SDK

Déploiement Python programmatique avec contrôle fin.

```python
from config import ConfigurationManager
from openstack_sdk.deployment_engine import OpenStackDeploymentEngine

manager = ConfigurationManager()
config = manager.load_config('ma-config.yaml')

engine = OpenStackDeploymentEngine(config)
result = engine.deploy_infrastructure()
```

Voir `openstack_sdk/README.md` pour les détails.

### Solution Ansible

Gestion de configuration avec playbooks idempotents.

```bash
ansible-playbook ansible/playbook.yml -e @vars.yml
```

Voir `ansible/README.md` pour les détails.

## Fonctionnalités

### Gestion de Configuration
- ✅ Support des formats YAML et JSON
- ✅ Substitution des variables d'environnement
- ✅ Validation complète avec erreurs descriptives
- ✅ Modèles de données pour tous les types de ressources

### Journalisation
- ✅ Journalisation structurée avec horodatages
- ✅ Niveaux de journalisation configurables (DEBUG, INFO, WARNING, ERROR)
- ✅ Sortie vers fichier et console
- ✅ Méthodes spécifiques à la journalisation du déploiement

### Sécurité
- Support des variables d'environnement pour les identifiants
- Pas d'identifiants codés en dur
- Gestion sécurisée des identifiants
- Configuration des groupes de sécurité
- Support des proxys pour les connexions HTTP et HTTPS

### Gestion des Ressources
- Réseaux et sous-réseaux
- Instances de calcul
- Volumes de stockage
- Groupes de sécurité
- IP flottantes (à venir)

## Développement

### Installer les Dépendances de Développement

```bash
pip install -r requirements-dev.txt
```

### Exécuter les Tests

```bash
pytest tests/ -v --cov=config --cov=utils
```

### Qualité du Code

```bash
# Formater le code
black .

# Vérifier le code
flake8 .

# Vérification de types
mypy config/ utils/
```

## Documentation

- `examples/README.md` - Exemples et référence de configuration
- `terraform/README.md` - Documentation de la solution Terraform
- `openstack_sdk/README.md` - Documentation de la solution OpenStack SDK
- `ansible/README.md` - Documentation de la solution Ansible

## Dépendances

### Dépendances Principales
- Python >= 3.8
- openstacksdk >= 1.0.0
- PyYAML >= 6.0

### Solution Terraform
- Terraform >= 1.5.0
- terraform-provider-openstack >= 1.51.0

### Solution Ansible
- Ansible >= 2.14.0
- Collection openstack.cloud >= 2.0.0

Voir `requirements.txt` et `requirements-dev.txt` pour les listes complètes des dépendances.

## Informations sur OVH OpenStack

### Régions Disponibles
- GRA7 (Gravelines, France)
- BHS5 (Beauharnois, Canada)
- DE1 (Francfort, Allemagne)
- UK1 (Londres, Royaume-Uni)
- WAW1 (Varsovie, Pologne)
- SBG5 (Strasbourg, France)

### Goûts d'Instances Courants
- scale-1: 24 vCore, 128MB RAM
- scale-2: 32 vCore, 256MB RAM
- scale-3: 48 vCore, 256MB RAM

### Types de Volumes
- classic : Performance standard
- high-speed : SSD haute performance

## Licence

[ajouter votre licence ici]

## Contribution

[ajouter les directives de contribution ici]

## Support

Pour les problèmes et questions :
- Documentation OVH : https://docs.ovh.com/
- Documentation OpenStack : https://docs.openstack.org/
- Problèmes du projet : [ajouter l'URL du gestionnaire de problèmes]