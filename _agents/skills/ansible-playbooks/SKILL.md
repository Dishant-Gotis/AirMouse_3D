---
skill_name: ansible-playbooks
description: Ansible roles, handlers, vault, dynamic inventory, molecule testing
category: Cloud & DevOps
version: 1.0.0
---

# Ansible Automation Patterns

## Role Structure and Best Practices

Organize Ansible playbooks as reusable roles.

```
roles/
├── webserver/
│   ├── defaults/
│   │   └── main.yml
│   ├── files/
│   ├── handlers/
│   │   └── main.yml
│   ├── meta/
│   │   └── main.yml
│   ├── tasks/
│   │   └── main.yml
│   ├── templates/
│   │   └── nginx.conf.j2
│   └── vars/
│       └── main.yml
└── database/
    ├── defaults/
    ├── handlers/
    ├── tasks/
    └── templates/
```

**tasks/main.yml**:

```yaml
---
- name: Install nginx
  become: yes
  ansible.builtin.package:
    name: nginx
    state: latest
    update_cache: yes

- name: Copy nginx configuration
  become: yes
  ansible.builtin.template:
    src: nginx.conf.j2
    dest: /etc/nginx/nginx.conf
    backup: yes
  notify: restart nginx

- name: Ensure nginx is running
  become: yes
  ansible.builtin.service:
    name: nginx
    state: started
    enabled: yes

- name: Verify nginx is accessible
  ansible.builtin.uri:
    url: http://localhost
    status_code: 200
  retries: 3
  delay: 5
```

**handlers/main.yml**:

```yaml
---
- name: restart nginx
  become: yes
  ansible.builtin.service:
    name: nginx
    state: restarted

- name: reload nginx
  become: yes
  ansible.builtin.service:
    name: nginx
    state: reloaded
```

## Vault for Secrets Management

Encrypt sensitive data with Ansible Vault.

```bash
# Create encrypted file
ansible-vault create group_vars/production/secrets.yml

# Edit encrypted file
ansible-vault edit group_vars/production/secrets.yml

# Encrypt existing file
ansible-vault encrypt existing_file.yml

# Decrypt file (not recommended)
ansible-vault decrypt secrets.yml

# View encrypted file
ansible-vault view secrets.yml
```

**Use in playbooks**:

```yaml
# playbook.yml
---
- name: Deploy application
  hosts: servers
  vars_files:
    - group_vars/production/secrets.yml
  tasks:
    - name: Configure database
      postgresql_user:
        name: app_user
        password: "{{ db_password }}"
        encrypted: yes
```

**Run with vault**:

```bash
# Prompt for vault password
ansible-playbook playbook.yml --ask-vault-pass

# Use vault password file
ansible-playbook playbook.yml --vault-password-file=~/.vault_pass

# Use environment variable
export ANSIBLE_VAULT_PASSWORD=mypassword
ansible-playbook playbook.yml
```

## Dynamic Inventory

Generate inventory from external sources.

```python
#!/usr/bin/env python3
# inventory.py
import json
import boto3

def get_inventory():
    ec2 = boto3.resource('ec2', region_name='us-east-1')
    instances = ec2.instances.filter(
        Filters=[
            {'Name': 'instance-state-name', 'Values': ['running']},
            {'Name': 'tag:ansible', 'Values': ['true']}
        ]
    )

    inventory = {
        '_meta': {'hostvars': {}},
        'webservers': {'hosts': [], 'vars': {}},
        'databases': {'hosts': [], 'vars': {}},
    }

    for instance in instances:
        host_ip = instance.private_ip_address
        tags = {tag['Key']: tag['Value'] for tag in instance.tags or []}

        hostvars = {
            'ansible_host': host_ip,
            'instance_id': instance.id,
            'instance_type': instance.instance_type
        }

        if tags.get('role') == 'webserver':
            inventory['webservers']['hosts'].append(host_ip)
        elif tags.get('role') == 'database':
            inventory['databases']['hosts'].append(host_ip)

        inventory['_meta']['hostvars'][host_ip] = hostvars

    return inventory

if __name__ == '__main__':
    print(json.dumps(get_inventory(), indent=2))
```

**Use dynamic inventory**:

```bash
ansible-inventory -i inventory.py --list
ansible-playbook -i inventory.py playbook.yml
```

## Molecule Testing

Test Ansible roles in Docker containers.

```bash
# Initialize test environment
molecule init role my-role

# Create test instances
molecule create

# Run playbook
molecule converge

# Verify idempotency
molecule idempotent

# Run tests
molecule verify

# Full lifecycle
molecule test
```

**molecule.yml**:

```yaml
---
driver:
  name: docker

platforms:
  - name: ubuntu-20.04
    image: ubuntu:20.04
    pre_build_image: true
    volumes:
      - /sys/fs/cgroup:/sys/fs/cgroup:ro
    cgroupns_mode: host
    privileged: true

  - name: ubuntu-22.04
    image: ubuntu:22.04
    pre_build_image: true

provisioner:
  name: ansible
  options:
    verbose: true
  inventory:
    group_vars:
      all:
        var: value

verifier:
  name: ansible
```

**Test playbook (verify.yml)**:

```yaml
---
- name: Verify
  hosts: all
  gather_facts: false
  tasks:
    - name: Check nginx is installed
      ansible.builtin.package_facts:
        manager: apt

    - name: Verify nginx package
      ansible.builtin.assert:
        that:
          - "'nginx' in ansible_facts.packages"
        fail_msg: "nginx not installed"

    - name: Check service is running
      ansible.builtin.service_facts:

    - name: Verify nginx service
      ansible.builtin.assert:
        that:
          - "ansible_facts.services['nginx.service']['state'] == 'running'"
```

## Handlers and Handlers Groups

Execute tasks when other tasks notify changes.

```yaml
---
- name: Configure application
  hosts: servers
  tasks:
    - name: Update configuration file
      ansible.builtin.template:
        src: app.conf.j2
        dest: /etc/app/config
      notify:
        - restart application
        - notify team

    - name: Update database schema
      postgresql_query:
        db: mydb
        query: "{{ item }}"
      loop: "{{ db_migrations }}"
      notify: rebuild cache

  handlers:
    - name: restart application
      ansible.builtin.service:
        name: app
        state: restarted
      listen: "restart application"

    - name: notify team
      ansible.builtin.uri:
        url: https://hooks.slack.com/services/YOUR/WEBHOOK
        method: POST
        body_format: json
        body:
          text: "Application restarted"
      listen: "restart application"

    - name: rebuild cache
      ansible.builtin.command: /opt/app/rebuild-cache.sh
      listen: "rebuild cache"
```

## Idempotent Playbooks

Write playbooks that can be safely run multiple times.

```yaml
---
- name: Deploy application idempotently
  hosts: servers
  tasks:
    - name: Check if user exists
      ansible.builtin.getent:
        database: passwd
        key: appuser
      ignore_errors: yes
      register: user_exists

    - name: Create user (if not exists)
      ansible.builtin.user:
        name: appuser
        shell: /bin/bash
        createhome: yes
      when: user_exists is failed

    - name: Ensure directory structure
      ansible.builtin.file:
        path: "{{ item }}"
        state: directory
        owner: appuser
        mode: '0755'
      loop:
        - /opt/app
        - /opt/app/config
        - /opt/app/data

    - name: Copy application (only if changed)
      ansible.builtin.copy:
        src: app/
        dest: /opt/app/
        owner: appuser
        group: appuser
        mode: '0755'
      register: app_copy

    - name: Restart app only if copied
      ansible.builtin.service:
        name: app
        state: restarted
      when: app_copy.changed
```

## Error Handling

Implement robust error handling strategies.

```yaml
---
- name: Robust error handling
  hosts: servers
  tasks:
    - name: Try to upgrade packages
      ansible.builtin.apt:
        upgrade: full
      rescue:
        - name: Handle upgrade failure
          ansible.builtin.debug:
            msg: "Package upgrade failed, retrying..."

        - name: Retry upgrade
          ansible.builtin.apt:
            upgrade: full
          retries: 3
          delay: 10

    - name: Deploy application with rollback
      block:
        - name: Download release
          ansible.builtin.get_url:
            url: "https://releases.example.com/app-{{ version }}.tar.gz"
            dest: /tmp/

        - name: Extract release
          ansible.builtin.unarchive:
            src: "/tmp/app-{{ version }}.tar.gz"
            dest: /opt/app/

        - name: Run tests
          ansible.builtin.command: /opt/app/test.sh
          changed_when: false

      rescue:
        - name: Rollback to previous version
          ansible.builtin.command: "git -C /opt/app checkout {{ previous_version }}"
          notify: restart application

        - name: Fail playbook
          ansible.builtin.fail:
            msg: "Deployment failed and rolled back"

      always:
        - name: Clean up temporary files
          ansible.builtin.file:
            path: "/tmp/app-*.tar.gz"
            state: absent
```

## Template Variables and Filters

Use Jinja2 templating for dynamic configuration.

```yaml
# templates/app.conf.j2
server {
    listen {{ server_port }};
    server_name {{ server_names | join(' ') }};

    location / {
        proxy_pass http://{{ backend_servers | join(',') }};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;

        {% if enable_caching %}
        proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=my_cache:10m;
        proxy_cache my_cache;
        {% endif %}
    }

    {% for location in special_locations %}
    location {{ location.path }} {
        proxy_pass {{ location.backend }};
    }
    {% endfor %}
}

# Access with filters
{{ some_string | upper }}
{{ items | selectattr('enabled') | list }}
{{ dict_var | to_json }}
```

## Conditionals and Loops

Advanced task execution control.

```yaml
---
- name: Conditional and loop tasks
  hosts: servers
  tasks:
    - name: Install packages for Ubuntu
      ansible.builtin.apt:
        name: "{{ ubuntu_packages }}"
      when: ansible_os_family == "Debian"

    - name: Install packages for RedHat
      ansible.builtin.yum:
        name: "{{ redhat_packages }}"
      when: ansible_os_family == "RedHat"

    - name: Create multiple users
      ansible.builtin.user:
        name: "{{ item.name }}"
        shell: "{{ item.shell }}"
        groups: "{{ item.groups | join(',') }}"
      loop: "{{ users }}"
      when: item.enabled

    - name: Configure multiple services
      ansible.builtin.template:
        src: "{{ item }}.j2"
        dest: "/etc/{{ item }}.conf"
      loop:
        - nginx
        - postgresql
        - redis
      notify: restart services
```

## Playbook Organization

Structure complex playbooks logically.

```yaml
# site.yml
---
- name: Deploy entire stack
  hosts: localhost
  gather_facts: no
  tasks:
    - name: Run infrastructure setup
      ansible.builtin.import_playbook: playbooks/infrastructure.yml

    - name: Run application deployment
      ansible.builtin.import_playbook: playbooks/application.yml

    - name: Run monitoring setup
      ansible.builtin.import_playbook: playbooks/monitoring.yml

    - name: Run health checks
      ansible.builtin.import_playbook: playbooks/healthcheck.yml
```

## Integration with CI/CD

Run Ansible from GitLab CI/GitHub Actions.

```yaml
# .gitlab-ci.yml
deploy:
  stage: deploy
  image: ansible:2.10
  script:
    - ansible-playbook -i inventory.yml site.yml --check
    - ansible-playbook -i inventory.yml site.yml
  only:
    - main
```
