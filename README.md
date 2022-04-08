# Deployment of OKD SINGLE NODE in the Yandex cloud
<ol>
<li>Создать сервисный аккаунт с именем
<pre><code>okd4-service-account</code></pre></li>
и выдать на данный аккаунт права: editor, storage.admin
<li>Создать виртуальную машину в Compute Cloud Fedora 34/35 и подключить к этой виртуальной машине созданный сервис аккаунт.</li>
<li>Склонировать к себе гит репозиторий</li>
<pre><code>git clone https://github.com/aluera/okd-yc-single-node.git</code></pre>
<li>В download-oc.sh выбрать какую версию OKD нужно установить.<pre><code>bash download-oc.sh</code></pre></li>
<li>Внести свои правки в файл config.py</li>
<li>Выполнить: <pre><code>python initial.py</code></pre></li>
</ol>