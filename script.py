import os, shutil, sys, time, subprocess, sh, datetime

temp_dir = './temp_dir'
media_dir = './media'
today = datetime.datetime.now()
cnt_f = 0

def remove(path):
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        print("Unable to remove file: %s" % path)


def cleanup(number_of_days, path):
    time_in_secs = time.time() - (number_of_days * 24 * 60 * 60)
    for root, dirs, files in os.walk(path, topdown=False):
        for file_ in files:
            full_path = os.path.join(root, file_)
            stat = os.stat(full_path)

            if stat.st_mtime <= time_in_secs:
                remove(full_path)

# vide le repertoire temporaire
cleanup(0, temp_dir)

# nettoie le repertoire de stockage
cleanup(15, media_dir)

# recupere les fichiers
subprocess.call(['youtube-dl', 
                 '-x', 
                 '--audio-format', 'mp3', 
                 '--add-metadata', 
                 '--playlist-end', '15', 
                 '--download-archive', './arch_file.txt', 
                 '--dateafter', 'now-10days', 
                 '-o', temp_dir + '/%(id)s.%(ext)s', 
                 'https://www.youtube.com/channel/UCK4YnDjmmMySzXSYYiHQDxw']
                 , shell=False)

# boucle sur les fichiers récupérés
for filename in os.listdir(temp_dir):
    if filename.endswith(".mp3"):
        cnt_f = cnt_f + 1
        # reencode pour prendre moins de place
        subprocess.call(['lame',
                         '--mp3input',
                         '-b', '32',
                         temp_dir + "/" + filename,
                         temp_dir + "/B_" + filename]
                         , shell=False)
        os.rename(temp_dir + "/B_" + filename, temp_dir + "/" + filename)
        # construction des items à ajouter dans le feed.xml
        titre = sh.cut(sh.grep(sh.ffprobe("-v", "error", "-show_format", temp_dir + "/" + filename),"title"),"-d","=","-f2")
        titre = str(titre)
        titre = titre.replace('\n','')
        fichier = open(temp_dir + "/" + "items.xml", "a")
        fichier.write("<item>\n")
        fichier.write("<title><![CDATA[" + titre + "]]></title>\n")
        fichier.write("<link>https://raw.githubusercontent.com/tcaenen/tt_pod/master/media/" + filename + "</link>\n")
        fichier.write('<enclosure url="https://raw.githubusercontent.com/tcaenen/tt_pod/master/media/' + filename + '" length="30066338" type="audio/mpeg"></enclosure>\n')
        fichier.write("<guid>https://raw.githubusercontent.com/tcaenen/tt_pod/master/media/" + filename + "</guid>\n")
        fichier.write("<author>tcaenen@gmail.com (tib)</author>\n")
        fichier.write("<itunes:author>tib</itunes:author>\n")
        fichier.write("<pubDate>" + today.strftime('%a, %d %b %Y %H:%M:%S') + " +0000</pubDate>\n")
        fichier.write("</item>\n")
        fichier.close()
        os.rename(temp_dir + "/" + filename, media_dir + "/" + filename)

if cnt_f > 0:
    # au moins un fichier

    # retire les 10 premieres et 3 dernieres lignes du feed
    feed = open("feed.xml")
    lines = feed.readlines()
    feed.close()
    feedw = open("feed.xml","w")
    feedw.writelines([item for item in lines[9:-3]])
    feedw.close()

    # ajoute les items
    f=open(temp_dir + "/" + "items.xml")
    f1=open("feed.xml","a")
    for x in f.readlines():
        f1.write(x)
    f.close()
    f1.close()

    # ajoute les 3 dernieres lignes de fermeture
    f2=open("feed.xml","a")
    f2.write("\n")
    f2.write("</channel>\n")
    f2.write("</rss>")
    f2.close()

    # maj la last build date
    f3=open("header_feed.xml","a")
    f3.write("<?xml version='1.0' encoding='utf-8'?>\n")
    f3.write("<rss xmlns:itunes='http://www.itunes.com/dtds/podcast-1.0.dtd' xml:lang='fr_FR' version='2.0' xmlns:atom='http://www.w3.org/2005/Atom'>\n")
    f3.write("<channel>\n")
    f3.write("<title>TrashTalk</title>\n")
    f3.write("<link>https://raw.githubusercontent.com/tcaenen/tt_pod/master/</link>\n")
    f3.write("<atom:link href='https://raw.githubusercontent.com/tcaenen/tt_pod/master/feed.xml' rel='self' type='application/rss+xml' />\n")
    f3.write("<description>nba podcast</description>\n")
    f3.write("<generator>Podcast Generator 3.0 - http://www.podcastgenerator.net</generator>\n")
    f3.write("<lastBuildDate>" + today.strftime('%a, %d %b %Y %H:%M:%S') + " +0000</lastBuildDate>\n")
    f3.close()

    # ajout du header
    f4=open("feed.xml")
    f5=open("header_feed.xml","a")
    for x in f4.readlines():
        f5.write(x)
    f4.close()
    f5.close()

    os.remove("feed.xml")
    os.rename("header_feed.xml", "feed.xml")
    os.remove(temp_dir + "/" + "items.xml")

    subprocess.call(['git',
                     'add', '*']
                     , shell=False)

    subprocess.call(['git',
                     'commit',
                     '-m',
                     '"update"']
                     , shell=False)

    subprocess.call(['git',
                     'push']
                     , shell=False)
