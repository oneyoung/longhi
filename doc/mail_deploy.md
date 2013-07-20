# Configure DKIM, SPR, PTR & SMTP


## SMTP server
Here I just choose postfix.
Someone on the Internet said the configuration was very complicated, but after I install postfix, I found the default config file is OK if you just want to send email from you locathost.

```bash
sudo apt-get install postfix
```

At first time when you test sending email, you might encount with such error:

```
postdrop: warning: unable to look up public/pickup: 
No such file or directory
```

That's because old sendmail daemon still running, just stop it and restart postfix can fix:
```bash
$ sudo /etc/init.d/sendmail stop 
$ sudo  mkfifo /var/spool/postfix/public/pickup
$ sudo /etc/init.d/postfix restart
```

## DNS `MX` field

Make sure your dns has MX field, here I don't add any prefix to my domain, just as the origin.
Here I take my domain 'one-young.com' for example.

```bash
$ dig -t MX one-young.com

;; ANSWER SECTION:
one-young.com.          3600    IN      MX      0 one-young.com.

```

## DKIM
### Add DKIM field to your domain record

#### First, install required packages (we need opendkim-tools in order to get i`opendkim-genkey`):

```bash
sudo apt-get install opendkim opendkim-tools
```

#### Generate keys for later use:

```bash
opendkim-genkey -r -d one-young.com -s default
# -r option indicate this key is for email use only, -d follow the domain.
# -s for selector name, that is to say you can have multiple keys,
#    and use the selector to determine which one to use.
#    here we just use 'default'
```
after run this command, will generate two file in current dir:

* 'SELECTOR.txt' -- public key, you need to add in your domain txt field
* 'SELECTOR.private' -- private key for opendkim use

Here, since we use 'default' as selector name, 'default.txt' & 'default.private' will be generated.

#### Add DKIM key to your domain

Below is the content of my default.txt

```
default._domainkey	IN	TXT	( "v=DKIM1; k=rsa; s=email; "
	  "p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDoyy7K+KFmXjuBMFtIpzMsfmouaI2479gbLMtixDRQAD3UBD58n9yPlpvYm9lRIlAUL4WgNRARA6CjTLBUdO6TMDsrYP3FhrgyWIB3HvesuZU+IVoGFq3FHDsCl+Ah9FiS9LsYWPo3UcMJB1g0Qeamm6e+uJrVe5UVUKKPYoJ+QwIDAQAB" )  ; ----- DKIM key default for one-young.com
```
So we can add a TXT entry in your domain record.

* host -- `SELECTOR._domainkey.YOURDOMAIN`, here we use `default._domainkey.one-young.com`
* value -- paste the content of `()`: `v=DKIM1; k=rsa; s=email; p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDoyy7K+KFmXjuBMFtIpzMsfmouaI2479gbLMtixDRQAD3UBD58n9yPlpvYm9lRIlAUL4WgNRARA6CjTLBUdO6TMDsrYP3FhrgyWIB3HvesuZU+IVoGFq3FHDsCl+Ah9FiS9LsYWPo3UcMJB1g0Qeamm6e+uJrVe5UVUKKPYoJ+QwIDAQAB`


Let's check out the result:

```bash
$ dig  -t txt default._domainkey.one-young.com

;; ANSWER SECTION:
default._domainkey.one-young.com. 3599 IN TXT   "v=DKIM1\; k=rsa\; s=email\; p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDoyy7K+KFmXjuBMFtIpzMsfmouaI2479gbLMtixDRQAD3UBD58n9yPlpvYm9lRIlAUL4WgNRARA6CjTLBUdO6TMDsrYP3FhrgyWIB3HvesuZU+IVoGFq3FHDsCl+Ah9FiS9LsYWPo3UcMJB1g0Qeamm6e+uJrVe5UVUKKPYoJ+QwIDAQAB"
```

#### have a check
[DkimCore](http://dkimcore.org/tools/) provide a good tools to valid your DNS dkim fields, you can have a check.

### use `opendkim` to sign your email

#### config opendkim
opendkim config locate in `/etc/opendkim.conf`, add the below fileds to your config file.
If you need more options, you can `man opendkim.conf` for more information.

```
# this is the uid of postfix, you can get by `id postfix`
UMask			107

# host config
ExternalIgnoreList      refile:/etc/opendkim/TrustedHosts
InternalHosts           refile:/etc/opendkim/TrustedHosts
KeyTable                refile:/etc/opendkim/KeyTable
SigningTable            refile:/etc/opendkim/SigningTable

# run in both signing and validate mode
Mode					sv

# we set up a socket for postfix dameon connection
Socket inet:9999@localhost

# misc config below, not necessary if you don't want
Canonicalization        relaxed/relaxed
SignatureAlgorithm      rsa-sha256

AutoRestart             yes
Background              yes

LogResults 		yes
Statistics              /var/log/dkim-stats
```

We can see in host config section, we add 3 files here.

* /etc/opendkim/TrustedHosts -- a list of servers to “trust” when signing or verifying
```
127.0.0.1
localhost
one-young.me
```

* /etc/opendkim/KeyTable -- seclector index to our keys. *make sure opendkim can access key files*: you can chown to opendkim `sudo chown opendkim PATH_TO_YOUR_PRIVATE_KEYS`
```
default._domainkey.one-young.com one-young.com:default:/var/db/dkim/default.private
```

* /etc/opendkim/SigningTable --  a list of domains and accounts allowed to sign. The below example means email at `one-young.com` domain should use default keys to sign.

```
*@one-young.com default._domainkey.one-young.com
```

#### After you have done this, you can restart opendkim to take effect

```bash
/etc/init.d/opendkim restart
```

#### config postfix to sign email by opendkim
add the below lines to `/etc/postfix/main.cf`

```
smtpd_milters= inet:localhost:9999
milter_default_action = accept
milter_protocol = 2
non_smtpd_milters = inet:localhost:9999

```
Remember, we created a socket in opendkim at port 9999, here we redirect postfix to it.

Be sure to restart postfix to take effect: `/etc/init.d/postfix restart`

#### test
Now you can have a try on sending email, and check if DKIM head added.

```bash
echo "test" | mail YOUR-OUTER-MAILBOX@xxx.com
```
if you have some problems, you can have a check at /var/log/mail.log


## Add `SPF` field to increase mail delivery rate
`SPF` is a txt field of domain record to check auth sending mail host.

* host -- domain name of you email host, typically MX record
* value -- `v=spf1 a mx ptr mx:one-young.com -all`

Let's check the result

```bash
$ dig -t txt one-young.com

;; ANSWER SECTION:
one-young.com.          3600    IN      TXT     "v=spf1 a mx ptr mx:one-young.com -all"

```

## Config `PTR` to enable reverse lookup

Your domain service provider should have such options, for me, in Godaddy, just click a memu.



Refs:
[1](http://www.quanlei.com/2012/06/3148.html)
[2](http://stevejenkins.com/blog/2010/09/how-to-get-dkim-domainkeys-identified-mail-working-on-centos-5-5-and-postfix-using-opendkim/)
[3](https://wiki.archlinux.org/index.php/OpenDKIM)
[4](http://linuxhostingsupport.net/blog/postfix-postdrop-unable-to-look-up-publicpickup-no-such-file-or-directory)
