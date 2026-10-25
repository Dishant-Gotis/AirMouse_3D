---
skill_name: Ansible Automation Guide
description: Automate infrastructure with Ansible playbooks, roles, inventory, vault encryption, and Galaxy collections
category: DevOps
version: 1.0.0
---

# Ansible Automation Guide

## Overview
Ansible provides agentless automation for configuration management. Master playbooks, roles, and inventory for reliable infrastructure as code.

## Playbook Fundamentals

### Basic Playbook Structure

```yaml
---
- name: Configure web servers
  hosts: webservers
  become: yes
  gather_facts: yes

  vars:
    nginx_version: 1.24
    app_port: 8080

  pre_tasks:
    - name: Update package cache
      apt:
        update_cache: yes
        cache_valid_time: 3600

  tasks:
    - name: Install Nginx
      apt:
        name: "nginx={{ nginx_version }}*"
        state: present
      notify: restart nginx

    - name: Create app directory
      file:
        path: /opt/app
        state: directory
        mode: '0755'
        owner: appuser
        group: appgroup

    - name: Copy application files
      copy:
        src: ./app/
        dest: /opt/app/
        owner: appuser
        group: appgroup
        mode: '0644'

    - name: Start application service
      systemd:
        name: myapp
        enabled: yes
        state: started

    - name: Configure Nginx reverse proxy
      template:
        src: nginx.conf.j2
        dest: /etc/nginx/sites-available/default
        backup: yes
      notify: restart nginx

  handlers:
    - name: restart nginx
      systemd:
        name: nginx
        state: restarted

  post_tasks:
    - name: Verify application health
      uri:
        url: "http://localhost:{{ app_port }}/health"
        status_code: 200
      retries: 5
      delay: 10
```

## Roles & Reusability

### Role Structure

```
roles/
├── webserver/
│   ├── tasks/
│   │   └── main.yml
│   ├── handlers/
│   │   └── main.yml
│   ├── templates/
│   │   └── nginx.conf.j2
│   ├── files/
│   │   └── default.conf
│   ├── vars/
│   │   └── main.yml
│   └── meta/
│       └── main.yml
```

### Role Example

```yaml
# roles/webserver/tasks/main.yml
---
- name: Install dependencies
  apt:
    name: "{{ packages }}"
    state: present
  vars:
    packages:
      - nginx
      - ssl-cert
      - curl

- name: Create document root
  file:
    path: "{{ doc_root }}"
    state: directory
    mode: '0755'

- name: Deploy configuration
  template:
    src: nginx.conf.j2
    dest: /etc/nginx/sites-available/default
  notify: restart nginx

# roles/webserver/handlers/main.yml
---
- name: restart nginx
  systemd:
    name: nginx
    state: restarted
    daemon_reload: yes

# roles/webserver/meta/main.yml
---
galaxy_info:
  author: DevOps Team
  description: Web server role
  company: Company
  license: MIT
  min_ansible_version: '2.10'
  platforms:
    - name: Ubuntu
      versions:
        - focal
        - jammy
```

### Using Roles in Playbooks

```yaml
---
- name: Deploy web tier
  hosts: webservers
  roles:
    - role: webserver
      vars:
        doc_root: /var/www/html

    - role: ssl-config
      vars:
        cert_domain: example.com

- name: Deploy database tier
  hosts: dbservers
  roles:
    - role: database
      vars:
        db_version: '14'
        db_name: production
```

## Inventory Management

### Dynamic Inventory

```yaml
# inventory/hosts.ini
[webservers]
web1.example.com
web2.example.com
web3.example.com

[webservers:vars]
nginx_port=80
ssl_enabled=true

[dbservers]
db1.example.com
db2.example.com

[dbservers:vars]
pg_version=14

[all:vars]
ansible_user=ubuntu
ansible_ssh_private_key_file=~/.ssh/id_rsa
ansible_python_interpreter=/usr/bin/python3
```

### AWS Dynamic Inventory

```yaml
# inventory/aws_ec2.yml
---
plugin: aws_ec2
regions:
  - us-east-1
  - us-west-2
keyed_groups:
  - prefix: env
    key: tags.Environment
  - prefix: role
    key: tags.Role
  - prefix: region
    key: placement.region
hostnames:
  - ip-address
  - private-ip-address
filters:
  tag:Project: my-project
  instance-state-name: running
compose:
  ansible_host: private_ip_address
```

## Vault & Secrets

### Encrypt Sensitive Data

```bash
# Encrypt a file
ansible-vault encrypt inventory/group_vars/dbservers/vault.yml

# Encrypt specific values
ansible-vault encrypt_string 'my-secret-password'

# Edit encrypted file
ansible-vault edit inventory/group_vars/dbservers/vault.yml
```

### Vault in Playbooks

```yaml
---
# vars/main.yml (encrypted with vault)
---
db_password: "{{ vault_db_password }}"
api_key: "{{ vault_api_key }}"

# playbook.yml
---
- name: Deploy application
  hosts: appservers
  vars_files:
    - vault/secrets.yml

  tasks:
    - name: Configure database connection
      template:
        src: app.config.j2
        dest: /etc/app/config.ini
      vars:
        - db_password: "{{ db_password }}"
```

## Conditionals & Loops

### Control Flow

```yaml
tasks:
  - name: Install package based on OS
    apt:
      name: nginx
      state: present
    when: ansible_os_family == "Debian"

  - name: Install package on specific OS version
    yum:
      name: nginx
      state: present
    when:
      - ansible_os_family == "RedHat"
      - ansible_distribution_major_version >= "7"

  - name: Create multiple users
    user:
      name: "{{ item }}"
      state: present
      groups: developers
    loop:
      - alice
      - bob
      - charlie

  - name: Configure services
    systemd:
      name: "{{ item.name }}"
      enabled: "{{ item.enabled }}"
      state: "{{ item.state }}"
    loop:
      - { name: 'nginx', enabled: true, state: 'started' }
      - { name: 'postgresql', enabled: true, state: 'started' }
      - { name: 'redis', enabled: false, state: 'stopped' }
```

## Ansible Galaxy

### Collection Management

```bash
# Install collection
ansible-galaxy collection install community.general

# Install from requirements
ansible-galaxy collection install -r requirements.yml
```

```yaml
# requirements.yml
---
collections:
  - name: community.general
    version: ">=5.0.0"
  - name: ansible.netcommon
  - name: amazon.aws
```

## Error Handling

```yaml
tasks:
  - name: Try to start service
    systemd:
      name: myservice
      state: started
    register: service_result
    ignore_errors: yes

  - name: Handle service failure
    debug:
      msg: "Service failed to start"
    when: service_result is failed

  - name: Rescue block example
    block:
      - name: Deploy application
        shell: ./deploy.sh
    rescue:
      - name: Rollback deployment
        shell: ./rollback.sh
    always:
      - name: Clean up
        shell: rm -rf /tmp/deploy/*
```

## Production Checklist

- [ ] Use roles for reusable automation
- [ ] Store secrets in Ansible Vault
- [ ] Use dynamic inventory for cloud resources
- [ ] Implement idempotent playbooks
- [ ] Use handlers for service restarts
- [ ] Test playbooks with --check flag
- [ ] Version control all playbooks
- [ ] Document variable requirements
- [ ] Use tags for selective execution
- [ ] Monitor playbook execution logs
