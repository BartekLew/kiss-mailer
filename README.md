kiss-sub
========

Very, very simple mailing written in CGI/Perl.

Usage
=====

Script can be used as GET & POST endpoint (according to
CGI, it can be emulated by setting $REQUEST_METHOD
environment variable).

Subscribtion request
--------------------

POST endpoint accepts message
body (it can be emulated by passing it through standard
input) with standard non-js HTML form data, like:

```
email=lew@wiedz.net.pl&name=Bartek Lew
```

these two fields are required and any other field is
ignored. Script stores this data along with random key
(used for confirmation) in file referenced by `$reqf`
("req.dat" by default). The key is sent to given address
using `$subtitle` as a title, `$submail` as an address
put into `FROM` field, `$linkbase` as a URL of the script
and `$template` with a name of file with a message template.

Subscription confirmation
-------------------------

GET endpoint accepts only key, like:

```
http://it.wiedz.net.pl/cgi-bin/sub.cgi?8cafe4f54d82e6074fd74ba01f8
```

if key matches one of found in `$reqf` file, the record is moved to
file referenced by `$subf` (`subs.dat` by default). The GET parameter
may be emulated using `$QUERY_STRING` environment variable.

Example form
------------

Script may be embedded in HTML page like this:

```
<!DOCTYPE html>
<html>
    <body>
        <form action="http://it.wiedz.net.pl/cgi-bin/sub.cgi" method="POST" target="_blank">
              Email: <input type="text" name="email"><br>
              Imię: <input type="text" name="name"><br>
              <input type="submit" value="subskrybuj">
        </form>
    </body>
</html>
```

and that's it. :)
