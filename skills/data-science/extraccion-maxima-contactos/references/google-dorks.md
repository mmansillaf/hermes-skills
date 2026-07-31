# Catalogo de Google Dorks para Extraccion de Contactos

## WEB: Documentos de contacto
```
site:objetivo.com filetype:xlsx "nombre" "telefono" "correo"
site:objetivo.com filetype:pdf "directorio" OR "anexo" OR "organigrama"
site:objetivo.com filetype:csv "DNI" OR "RUC" OR "celular"
site:objetivo.com intitle:"index of" "contacts" (csv OR xlsx OR vcf)
```

## WEB: Backups y configuraciones
```
site:objetivo.com ext:bak OR ext:old OR ext:backup OR ext:zip OR ext:sql
site:objetivo.com ext:env "DB_PASSWORD" OR "API_KEY"
site:objetivo.com inurl:phpmyadmin OR inurl:admin OR inurl:login
```

## CLOUD LEAKS
```
site:s3.amazonaws.com "empresa" filetype:csv OR filetype:xlsx
site:blob.core.windows.net "contactos" OR "directorio"
```

## PASTE SITES
```
site:pastebin.com "empresa.com" password
site:ideone.com "@empresa.com"
site:justpaste.it "empresa.com" email
```

## GITHUB
```
site:github.com "empresa.com" (password OR api_key OR smtp)
site:github.com "@empresa.com" filename:config
site:github.com "empresa.com" "connectionString" OR "DB_PASSWORD"
```

## VCARD / CALENDAR
```
intitle:"index of" "vcf" OR "vcard"
"BEGIN:VCARD" "EMAIL" "@empresa.com"
site:empresa.com ext:ics "ORGANIZER" "ATTENDEE"
```

## PERU ESPECIFICO
```
site:osce.gob.pe OR site:seace.gob.pe filetype:pdf "representante legal" "telefono"
site:gob.pe filetype:xlsx "directorio" "anexo" "telefono"
site:jne.gob.pe filetype:pdf "hoja de vida" "celular"
"RUC" "telefono" "correo" filetype:xlsx OR filetype:csv
site:*.gob.pe "correo electronico" OR "email" filetype:xls OR filetype:xlsx
site:indecopi.gob.pe filetype:pdf "denunciante" "domicilio"
```

## AD / EXCHANGE / O365
```
site:objetivo.com inurl:/owa OR inurl:/ecp OR inurl:/autodiscover
site:objetivo.com intitle:"Outlook Web App" OR intitle:"Exchange"
site:objetivo.com inurl:/adfs/ls OR inurl:/certsrv
site:objetivo.com intitle:"index of" ".git"
```

## LINKEDIN
```
site:linkedin.com/in "empresa.com" ("gerente" OR "director" OR "abogado")
site:linkedin.com/in "Perú" "@gmail.com" OR "@hotmail.com"
```

## HUBSPOT / MARKETING
```
site:hsforms.com "email" "phone" "company"
site:empresa.com filetype:js "hubspot" "portalId"
site:force.com "guest" "profile"
```
