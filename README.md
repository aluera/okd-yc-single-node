# Deployment of OKD SINGLE NODE in the Yandex cloud
<ol>
<li>Создать виртуальную машину в Compute Cloud Fedora 34/35 и подключить к этой виртуальной машине созданный сервис аккаунт c правами:
<pre><code>editor, storage.admin </code></pre></li></li>
<li>Склонировать к себе гит репозиторий:</li>
<pre><code>git clone https://github.com/aluera/okd-yc-single-node.git</code></pre>
<li>Запустить download-oc.sh и выбрать версию OKD:<pre><code>bash download-oc.sh</code></pre></li>
<li>Внести свои правки в файл:<pre><code>terraform-conf.tfvars</code></pre></li></li>
<li>Выполнить: <pre><code>python create_okd.py</code></pre></li>
</ol>
