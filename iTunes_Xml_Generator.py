#!/usr/bin/python
# -*- coding: utf-8 -*-

# iTunes Xml Generator
#
# Author: Simon Lachaîne


import codecs
import hashlib
import os
import sys
import time

import lxml.etree as etree
from PyQt4 import QtCore, QtGui
from unidecode import unidecode

import iTunes_genres as genres
import iTunes_ratings as ratings
import itunes_xml_generator_globals as settings
import languages_complete as languages_list
import ui_generator as main_frame
import ixg_about as about_dlg


def read_rng():
    settings.relaxng_doc = etree.parse("film5.2-strict.rng")


def create_countries():
    tree = etree.parse("ISO_country_codes.xml")
    for entry in tree.findall(path=".//ISO_3166-1_Entry"):
        country = entry.findtext(".//ISO_3166-1_Country_name")
        code = entry.findtext(".//ISO_3166-1_Alpha-2_Code_element")
        settings.countries[country] = code


def create_list(subject_lst, dict):
    """
    Creates a list from the dictionary of languages
    :return: list of language initials with their name
    """
    subject_lst = []
    for i in dict:
        subject_lst.append(i + ": " + dict[i])
    subject_lst.sort()
    return subject_lst


def create_providers():
    """
    Creates a list of providers from the reference text file
    :return: list of providers
    """
    providers_dic = {}

    try:
        with codecs.open("providers.txt", "r", encoding="utf8") as providers_text:
            for line in providers_text:
                try:
                    int(line[0])
                    line1 = line[4:].rstrip().split("  ")
                    providers_dic[line1[0]] = line1[-1].strip()

                except ValueError:
                    pass

        for i in providers_dic:
            settings.providers_lst.append(i + ": " + providers_dic[i])
        settings.providers_lst.sort()
        return settings.providers_lst

    except IOError:
        settings.providers_txt_missing = True


def hashfile(afile, hasher, blocksize=65536):
    """
    Generates checksums
    :param afile: file to process
    :param hasher: checksum algorithm
    :param blocksize: size of the buffer
    :return: checksum
    """
    buf = afile.read(blocksize)
    while len(buf) > 0:
        hasher.update(buf)
        buf = afile.read(blocksize)
    afile.seek(0)
    return hasher.hexdigest()


class FeatureMd5(QtCore.QThread):

    def __init__(self):
        QtCore.QThread.__init__(self)

    def __del__(self):
        self.wait()

    def run(self):
        settings.feature_md5 = hashfile(open(settings.feature_file_path, 'rb'), hashlib.md5())


class TrailerMd5(QtCore.QThread):

    def __init__(self):
        QtCore.QThread.__init__(self)

    def __del__(self):
        self.wait()

    def run(self):
        settings.trailer_md5 = hashfile(open(settings.trailer_file_path, 'rb'), hashlib.md5())


class LocTrailerMd5(QtCore.QThread):

    def __init__(self):
        QtCore.QThread.__init__(self)

    def __del__(self):
        self.wait()

    def run(self):
        settings.loc_trailer_md5 = hashfile(open(settings.loc_trailer_file_path, 'rb'), hashlib.md5())


class CreateXml(QtCore.QThread):

    def __init__(self):
        QtCore.QThread.__init__(self)

    def __del__(self):
        self.wait()

    def run(self):
        nsmap1 = {None: "http://apple.com/itunes/importer"}
        xml_root = etree.Element("package", attrib={"version": "film5.2"}, nsmap=nsmap1)
        xml_provider = etree.SubElement(xml_root, "provider")
        xml_provider.text = settings.provider

        # metadata
        if settings.meta:
            xml_language_meta = etree.SubElement(xml_root, "language")
            xml_language_meta.text = settings.language_meta
            xml_video = etree.SubElement(xml_root, "video")
            xml_type = etree.SubElement(xml_video, "type")
            xml_type.text = "film"
            xml_subtype = etree.SubElement(xml_video, "subtype")
            xml_subtype.text = "feature"
            xml_vendor = etree.SubElement(xml_video, "vendor_id")
            xml_vendor.text = settings.vendor
            xml_country = etree.SubElement(xml_video, "country")
            xml_country.text = settings.country
            xml_spoken = etree.SubElement(xml_video, "original_spoken_locale")
            xml_spoken.text = settings.spoken
            xml_title = etree.SubElement(xml_video, "title")
            xml_title.text = settings.title
            xml_studio_title = etree.SubElement(xml_video, "studio_release_title")
            xml_studio_title.text = settings.studio_title
            xml_synopsis = etree.SubElement(xml_video, "synopsis")
            xml_synopsis.text = settings.synopsis

            if any([settings.localized_check_1, 
                    settings.localized_check_2, 
                    settings.localized_check_3,
                    settings.localized_check_4]):
                xml_locales = etree.SubElement(xml_video, "locales")
                
                def localize_meta(localized_locale, localized_title, localized_synopsis):
                    xml_locale = etree.SubElement(xml_locales, "locale",
                                                       attrib={"name": localized_locale})
                    xml_localized_title = etree.SubElement(xml_locale, "title")
                    xml_localized_title.text = localized_title
                    xml_localized_synopsis = etree.SubElement(xml_locale, "synopsis")
                    xml_localized_synopsis.text = localized_synopsis

                if settings.localized_check_1:
                    localize_meta(
                        settings.localized_locale_1, 
                        settings.localized_title_1, 
                        settings.localized_synopsis_1)

                if settings.localized_check_2:
                    localize_meta(
                        settings.localized_locale_2,
                        settings.localized_title_2,
                        settings.localized_synopsis_2)

                if settings.localized_check_3:
                    localize_meta(
                        settings.localized_locale_3,
                        settings.localized_title_3,
                        settings.localized_synopsis_3)

                if settings.localized_check_4:
                    localize_meta(
                        settings.localized_locale_4,
                        settings.localized_title_4,
                        settings.localized_synopsis_4)
                
            xml_company = etree.SubElement(xml_video, "production_company")
            xml_company.text = settings.company
            xml_cline = etree.SubElement(xml_video, "copyright_cline")
            xml_cline.text = settings.cline
            xml_theatrical = etree.SubElement(xml_video, "theatrical_release_date")
            xml_theatrical.text = settings.theatrical

            self.emit(QtCore.SIGNAL("meta_done"))

        if settings.genres_ratings:
            if not settings.meta:
                xml_video = etree.SubElement(xml_root, "video")
                xml_type = etree.SubElement(xml_video, "type")
                xml_type.text = "film"
                xml_subtype = etree.SubElement(xml_video, "subtype")
                xml_subtype.text = "feature"
                xml_vendor = etree.SubElement(xml_video, "vendor_id")
                xml_vendor.text = settings.vendor

            xml_genres = etree.SubElement(xml_video, "genres")

            if settings.genre1 != "":
                xml_genre1 = etree.SubElement(xml_genres, "genre", attrib={"code": settings.genre1})

            if settings.genre2 != "":
                xml_genre2 = etree.SubElement(xml_genres, "genre", attrib={"code": settings.genre2})

            if settings.genre3 != "":
                xml_genre3 = etree.SubElement(xml_genres, "genre", attrib={"code": settings.genre3})

            if settings.genre4 != "":
                xml_genre4 = etree.SubElement(xml_genres, "genre", attrib={"code": settings.genre4})

            if settings.genre5 != "":
                xml_genre5 = etree.SubElement(xml_genres, "genre", attrib={"code": settings.genre5})

            if settings.genre6 != "":
                xml_genre6 = etree.SubElement(xml_genres, "genre", attrib={"code": settings.genre6})

            if settings.genre7 != "":
                xml_genre7 = etree.SubElement(xml_genres, "genre", attrib={"code": settings.genre7})

            if settings.genre8 != "":
                xml_genre8 = etree.SubElement(xml_genres, "genre", attrib={"code": settings.genre8})

            xml_ratings = etree.SubElement(xml_video, "ratings")

            if settings.rating1_sys != "":
                xml_rating1 = etree.SubElement(
                    xml_ratings,
                    "rating",
                    attrib={"system": settings.rating1_sys, "code": settings.rating1_value})

            if settings.rating2_sys != "":
                xml_rating2 = etree.SubElement(
                    xml_ratings,
                    "rating",
                    attrib={"system": settings.rating2_sys, "code": settings.rating2_value})

            if settings.rating3_sys != "":
                xml_rating3 = etree.SubElement(
                    xml_ratings,
                    "rating",
                    attrib={"system": settings.rating3_sys, "code": settings.rating3_value})

            if settings.rating4_sys != "":
                xml_rating4 = etree.SubElement(
                    xml_ratings,
                    "rating",
                    attrib={"system": settings.rating4_sys, "code": settings.rating4_value})

            if settings.rating5_sys != "":
                xml_rating5 = etree.SubElement(
                    xml_ratings,
                    "rating",
                    attrib={"system": settings.rating5_sys, "code": settings.rating5_value})

            self.emit(QtCore.SIGNAL("genres_ratings_done"))

        if settings.cast_crew:
            if not settings.meta and not settings.genres_ratings:
                if not settings.meta:
                    xml_video = etree.SubElement(xml_root, "video")
                    xml_type = etree.SubElement(xml_video, "type")
                    xml_type.text = "film"
                    xml_subtype = etree.SubElement(xml_video, "subtype")
                    xml_subtype.text = "feature"
                    xml_vendor = etree.SubElement(xml_video, "vendor_id")
                    xml_vendor.text = settings.vendor

            xml_cast = etree.SubElement(xml_video, "cast")

            def create_cast(
                    actor_name,
                    apple_id,
                    character_name,
                    character_name2,
                    reference_id,
                    reference_id2):
                xml_cast_member = etree.SubElement(xml_cast, "cast_member", attrib={"billing": "top"})

                if actor_name != "":
                    xml_cast_display = etree.SubElement(xml_cast_member, "display_name")
                    xml_cast_display.text = actor_name

                if apple_id != "":
                    xml_cast_apple_id = etree.SubElement(xml_cast_member, "apple_id")
                    xml_cast_apple_id.text = apple_id

                xml_characters = etree.SubElement(xml_cast_member, "characters")
                xml_char = etree.SubElement(xml_characters, "character")
                xml_char_name = etree.SubElement(xml_char, "character_name")
                xml_char_name.text = character_name
                xml_ref_id = etree.SubElement(xml_char, "reference_id")
                xml_ref_id.text = reference_id

                if character_name2 != "":
                    xml_char2 = etree.SubElement(xml_characters, "character")
                    xml_char_name2 = etree.SubElement(xml_char2, "character_name")
                    xml_char_name2.text = character_name2
                    xml_ref_id2 = etree.SubElement(xml_char2, "reference_id")
                    xml_ref_id2.text = reference_id2

            if settings.actor1_name != "" or settings.actor1_apple_id != "":
                create_cast(
                    settings.actor1_name,
                    settings.actor1_apple_id,
                    settings.actor1_char,
                    settings.actor1_char2,
                    settings.actor1_ref,
                    settings.actor1_ref2)

            if settings.actor2_name != "" or settings.actor2_apple_id != "":
                create_cast(
                    settings.actor2_name,
                    settings.actor2_apple_id,
                    settings.actor2_char,
                    settings.actor2_char2,
                    settings.actor2_ref,
                    settings.actor2_ref2)

            if settings.actor3_name != "" or settings.actor3_apple_id != "":
                create_cast(
                    settings.actor3_name,
                    settings.actor3_apple_id,
                    settings.actor3_char,
                    settings.actor3_char2,
                    settings.actor3_ref,
                    settings.actor3_ref2)

            if settings.actor4_name != "" or settings.actor4_apple_id != "":
                create_cast(
                    settings.actor4_name,
                    settings.actor4_apple_id,
                    settings.actor4_char,
                    settings.actor4_char2,
                    settings.actor4_ref,
                    settings.actor4_ref2)

            if settings.actor5_name != "" or settings.actor5_apple_id != "":
                create_cast(
                    settings.actor5_name,
                    settings.actor5_apple_id,
                    settings.actor5_char,
                    settings.actor5_char2,
                    settings.actor5_ref,
                    settings.actor5_ref2)

            if settings.actor6_name != "" or settings.actor6_apple_id != "":
                create_cast(
                    settings.actor6_name,
                    settings.actor6_apple_id,
                    settings.actor6_char,
                    settings.actor6_char2,
                    settings.actor6_ref,
                    settings.actor6_ref2)

            if settings.actor7_name != "" or settings.actor7_apple_id != "":
                create_cast(
                    settings.actor7_name,
                    settings.actor7_apple_id,
                    settings.actor7_char,
                    settings.actor7_char2,
                    settings.actor7_ref,
                    settings.actor7_ref2)

            if settings.actor8_name != "" or settings.actor8_apple_id != "":
                create_cast(
                    settings.actor8_name,
                    settings.actor8_apple_id,
                    settings.actor8_char,
                    settings.actor8_char2,
                    settings.actor8_ref,
                    settings.actor8_ref2)

            if settings.actor9_name != "" or settings.actor9_apple_id != "":
                create_cast(
                    settings.actor9_name,
                    settings.actor9_apple_id,
                    settings.actor9_char,
                    settings.actor9_char2,
                    settings.actor9_ref,
                    settings.actor9_ref2)

            if settings.actor10_name != "" or settings.actor10_apple_id != "":
                create_cast(
                    settings.actor10_name,
                    settings.actor10_apple_id,
                    settings.actor10_char,
                    settings.actor10_char2,
                    settings.actor10_ref,
                    settings.actor10_ref2)

            xml_crew = etree.SubElement(xml_video, "crew")

            def create_crew(crew_name, crew_apple_id, director, producer, screenwriter, composer, codirector):
                xml_crew_member = etree.SubElement(xml_crew, "crew_member", attrib={"billing": "top"})

                if crew_name != "":
                    xml_crew_display = etree.SubElement(xml_crew_member, "display_name")
                    xml_crew_display.text = crew_name

                if crew_apple_id != "":
                    xml_crew_apple_id = etree.SubElement(xml_crew_member, "apple_id")
                    xml_crew_apple_id.text = crew_apple_id

                xml_crew_roles = etree.SubElement(xml_crew_member, "roles")

                if director:
                    xml_crew_director = etree.SubElement(xml_crew_roles, "role")
                    xml_crew_director.text = "Director"

                if producer:
                    xml_crew_producer = etree.SubElement(xml_crew_roles, "role")
                    xml_crew_producer.text = "Producer"

                if screenwriter:
                    xml_crew_screenwriter = etree.SubElement(xml_crew_roles, "role")
                    xml_crew_screenwriter.text = "Screenwriter"

                if composer:
                    xml_crew_composer = etree.SubElement(xml_crew_roles, "role")
                    xml_crew_composer.text = "Composer"

                if codirector:
                    xml_crew_codirector = etree.SubElement(xml_crew_roles, "role")
                    xml_crew_codirector.text = "Co-Director"

            if settings.crew1_name != "" or settings.crew1_apple_id != "":
                create_crew(
                    settings.crew1_name,
                    settings.crew1_apple_id,
                    settings.crew1_director,
                    settings.crew1_producer,
                    settings.crew1_screenwriter,
                    settings.crew1_composer,
                    settings.crew1_codirector)

            if settings.crew2_name != "" or settings.crew2_apple_id != "":
                create_crew(
                    settings.crew2_name,
                    settings.crew2_apple_id,
                    settings.crew2_director,
                    settings.crew2_producer,
                    settings.crew2_screenwriter,
                    settings.crew2_composer,
                    settings.crew2_codirector)

            if settings.crew3_name != "" or settings.crew3_apple_id != "":
                create_crew(
                    settings.crew3_name,
                    settings.crew3_apple_id,
                    settings.crew3_director,
                    settings.crew3_producer,
                    settings.crew3_screenwriter,
                    settings.crew3_composer,
                    settings.crew3_codirector)

            if settings.crew4_name != "" or settings.crew4_apple_id != "":
                create_crew(
                    settings.crew4_name,
                    settings.crew4_apple_id,
                    settings.crew4_director,
                    settings.crew4_producer,
                    settings.crew4_screenwriter,
                    settings.crew4_composer,
                    settings.crew4_codirector)

            if settings.crew5_name != "" or settings.crew5_apple_id != "":
                create_crew(
                    settings.crew5_name,
                    settings.crew5_apple_id,
                    settings.crew5_director,
                    settings.crew5_producer,
                    settings.crew5_screenwriter,
                    settings.crew5_composer,
                    settings.crew5_codirector)

            if settings.crew6_name != "" or settings.crew6_apple_id != "":
                create_crew(
                    settings.crew6_name,
                    settings.crew6_apple_id,
                    settings.crew6_director,
                    settings.crew6_producer,
                    settings.crew6_screenwriter,
                    settings.crew6_composer,
                    settings.crew6_codirector)

            if settings.crew7_name != "" or settings.crew7_apple_id != "":
                create_crew(
                    settings.crew7_name,
                    settings.crew7_apple_id,
                    settings.crew7_director,
                    settings.crew7_producer,
                    settings.crew7_screenwriter,
                    settings.crew7_composer,
                    settings.crew7_codirector)

            if settings.crew8_name != "" or settings.crew8_apple_id != "":
                create_crew(
                    settings.crew8_name,
                    settings.crew8_apple_id,
                    settings.crew8_director,
                    settings.crew8_producer,
                    settings.crew8_screenwriter,
                    settings.crew8_composer,
                    settings.crew8_codirector)

            if settings.crew9_name != "" or settings.crew9_apple_id != "":
                create_crew(
                    settings.crew9_name,
                    settings.crew9_apple_id,
                    settings.crew9_director,
                    settings.crew9_producer,
                    settings.crew9_screenwriter,
                    settings.crew9_composer,
                    settings.crew9_codirector)

            if settings.crew10_name != "" or settings.crew10_apple_id != "":
                create_crew(
                    settings.crew10_name,
                    settings.crew10_apple_id,
                    settings.crew10_director,
                    settings.crew10_producer,
                    settings.crew10_screenwriter,
                    settings.crew10_composer,
                    settings.crew10_codirector)

        self.emit(QtCore.SIGNAL("cast_crew_done"))

        if settings.chapters:
            if settings.meta:
                # chapters
                xml_chapters = etree.SubElement(xml_video, "chapters")
                xml_tc = etree.SubElement(xml_chapters, "timecode_format")
                xml_tc.text = settings.timecodes.get(settings.tc_format)

                def chapter_template(timecode, count, thumbnail):
                    xml_chapter = etree.SubElement(xml_chapters, "chapter")
                    xml_start = etree.SubElement(xml_chapter, "start_time")
                    xml_start.text = timecode
                    xml_chapter_titles = etree.SubElement(xml_chapter, "titles")

                    def create_chapter_title(language):
                        xml_chapter_title = etree.SubElement(xml_chapter_titles, "title",
                                                             attrib={"locale": language})

                        if language[:2] == "af":
                            xml_chapter_title.text = u"Hoofstuk %s" % count
                        elif language[:2] == "ar":
                            xml_chapter_title.text = str(count) + u" باب"
                        elif language[:2] == "bg":
                            xml_chapter_title.text = u"Страница %s" % count
                        elif language[:2] == "ca":
                            xml_chapter_title.text = u"Capítol %s" % count
                        elif language[:8] == "cmn-Hans":
                            xml_chapter_title.text = u"章节 %s" % count
                        elif language[:8] == "cmn-Hant":
                            xml_chapter_title.text = u"章節 %s" % count
                        elif language[:2] == "cs":
                            xml_chapter_title.text = u"Kapitola %s" % count
                        elif language[:2] == "da" or language[:2] == "de" or language[:2] == "sv":
                            xml_chapter_title.text = u"Kapitel %s" % count
                        elif language[:2] == "el":
                            xml_chapter_title.text = u"Κεφάλαιο %s" % count
                        elif language[:2] == "es" or language[:2] == "pt":
                            xml_chapter_title.text = u"Capítulo %s" % count
                        elif language[:2] == "et":
                            xml_chapter_title.text = u"Peatükk %s" % count
                        elif language[:2] == "fi":
                            xml_chapter_title.text = u"Luku %s" % count
                        elif language[:2] == "fr":
                            xml_chapter_title.text = u"Chapitre %s" % count
                        elif language[:2] == "he":
                            xml_chapter_title.text = str(count) + u" פֶּרֶק"
                        elif language[:2] == "hi":
                            xml_chapter_title.text = u"अध्याय %s" % count
                        elif language[:2] == "hr":
                            xml_chapter_title.text = u"Poglavlje %s" % count
                        elif language[:2] == "hu":
                            xml_chapter_title.text = u"Fejezet %s" % count
                        elif language[:2] == "id" or language[:2] == "ms":
                            xml_chapter_title.text = u"Bab %s" % count
                        elif language[:2] == "is":
                            xml_chapter_title.text = u"Kafla %s" % count
                        elif language[:2] == "it":
                            xml_chapter_title.text = u"Capitolo %s" % count
                        elif language[:2] == "ja":
                            xml_chapter_title.text = u"チャプター %s" % count
                        elif language[:2] == "kk":
                            xml_chapter_title.text = u"Тарау %s" % count
                        elif language[:2] == "ko":
                            xml_chapter_title.text = u"장 %s" % count
                        elif language[:2] == "lb":
                            xml_chapter_title.text = u"Véiert %s" % count
                        elif language[:2] == "lo":
                            xml_chapter_title.text = u"ບົດ %s" % count
                        elif language[:2] == "lt":
                            xml_chapter_title.text = u"Skyrius %s" % count
                        elif language[:2] == "lv":
                            xml_chapter_title.text = u"Nodaļa %s" % count
                        elif language[:2] == "mt":
                            xml_chapter_title.text = u"Kapitolu %s" % count
                        elif language[:2] == "nl":
                            xml_chapter_title.text = u"Hoofdstuk %s" % count
                        elif language[:2] == "no":
                            xml_chapter_title.text = u"Kapittel %s" % count
                        elif language[:2] == "pl":
                            xml_chapter_title.text = u"Rozdział %s" % count
                        elif language[:2] == "ro":
                            xml_chapter_title.text = u"Capitol %s" % count
                        elif language[:2] == "ru":
                            xml_chapter_title.text = u"Глава %s" % count
                        elif language[:2] == "sk":
                            xml_chapter_title.text = u"Kapitola %s" % count
                        elif language[:2] == "sl":
                            xml_chapter_title.text = u"Poglavje %s" % count
                        elif language[:2] == "ta":
                            xml_chapter_title.text = u"அத்தியாயம் %s" % count
                        elif language[:2] == "te":
                            xml_chapter_title.text = u"అధ్యాయం %s" % count
                        elif language[:2] == "th":
                            xml_chapter_title.text = u"บท %s" % count
                        elif language[:2] == "tr":
                            xml_chapter_title.text = u"Bölüm %s" % count
                        elif language[:2] == "uk":
                            xml_chapter_title.text = u"Глава %s" % count
                        elif language[:2] == "ur":
                            xml_chapter_title.text = str(count) + u" باب"
                        elif language[:2] == "vi":
                            xml_chapter_title.text = u"Chương %s" % count
                        elif language[:2] == "zu":
                            xml_chapter_title.text = u"Isahluko %s" % count
                        else:
                            xml_chapter_title.text = u"Chapter %s" % count

                    for value in settings.chapter_locales.values():
                        create_chapter_title(value.split(":", 1)[0])

                    xml_chap_thumb = etree.SubElement(xml_chapter, "artwork_time")
                    xml_chap_thumb.text = thumbnail

                chapter_number = 0
                for i in range(len(settings.chapters_tc.keys())):
                    chapter_number += 1
                    chapter_template(settings.chapters_tc.values()[i], chapter_number, settings.thumbs_tc.values()[i])

                # accessibility info
                if (settings.product1_terr == "US" and settings.product1_check) \
                    or (settings.product2_terr == "US" and settings.product2_check) \
                    or (settings.product3_terr == "US" and settings.product3_check) \
                    or (settings.product4_terr == "US" and settings.product4_check):
                    xml_access_info = etree.SubElement(xml_video, "accessibility_info")

                    if settings.feat_asset1_role == "captions" \
                            or settings.feat_asset2_role == "captions" \
                            or settings.feat_asset3_role == "captions" \
                            or settings.feat_asset3_role == "captions" \
                            or settings.feat_asset4_role == "captions" \
                            or settings.feat_asset5_role == "captions" \
                            or settings.feat_asset6_role == "captions" \
                            or settings.feat_asset7_role == "captions" \
                            or settings.feat_asset8_role == "captions":
                        xml_access = etree.SubElement(
                            xml_access_info,
                            "accessibility",
                            attrib={"role": "captions", "available": "true"})

                    else:
                        xml_access = etree.SubElement(
                            xml_access_info,
                            "accessibility",
                            attrib={
                                "role": "captions",
                                "available": "false",
                                "reason_code": "NO_CC_SDH_FOREIGN_LANGUAGE_ENGLISH_SUBS"})

                settings.chapters_done = True
                self.emit(QtCore.SIGNAL("chapters_done"))

        if settings.feature:
            if settings.feature and not settings.meta:
                xml_assets = etree.SubElement(xml_root, "assets",
                                              attrib={"media_type": "video", "vendor_id": settings.vendor})

            elif settings.feature and settings.meta:
                xml_assets = etree.SubElement(xml_video, "assets")

            xml_asset_feat = etree.SubElement(xml_assets, "asset", attrib={"type": "full"})
            xml_feature = etree.SubElement(xml_asset_feat, "data_file", attrib={"role": "source"})
            xml_feat_locale = etree.SubElement(xml_feature, "locale", attrib={"name": settings.feature_audio})
            xml_feat_file = etree.SubElement(xml_feature, "file_name")
            xml_feat_file.text = settings.feature_file
            xml_feat_size = etree.SubElement(xml_feature, "size")
            xml_feat_size.text = str(os.path.getsize(settings.feature_file_path))
            xml_feat_md5 = etree.SubElement(xml_feature, "checksum",
                                            attrib={"type": "md5"})

            if settings.feature_md5 == "":
                settings.feature_md5 = hashfile(open(settings.feature_file_path, 'rb'), hashlib.md5())
                xml_feat_md5.text = settings.feature_md5

            else:
                xml_feat_md5.text = settings.feature_md5

            xml_feat_top = etree.SubElement(xml_feature, "attribute", attrib={"name": "crop.top"})
            xml_feat_top.text = settings.feat_crop_top
            xml_feat_bot = etree.SubElement(xml_feature, "attribute", attrib={"name": "crop.bottom"})
            xml_feat_bot.text = settings.feat_crop_bottom
            xml_feat_left = etree.SubElement(xml_feature, "attribute", attrib={"name": "crop.left"})
            xml_feat_left.text = settings.feat_crop_left
            xml_feat_right = etree.SubElement(xml_feature, "attribute", attrib={"name": "crop.right"})
            xml_feat_right.text = settings.feat_crop_right
            xml_feat_text = etree.SubElement(xml_feature, "attribute", attrib={"name": "image.textless_master"})

            if settings.feat_check_narr or settings.feat_check_subs:
                xml_feat_text.text = "false"

                if settings.feat_check_narr:
                    xml_feat_narr = etree.SubElement(
                        xml_feature, "attribute", attrib={"name": "image.burned_forced_narrative.locale"})
                    xml_feat_narr.text = settings.narr_feat

                if settings.feat_check_subs:
                    xml_feat_subs = etree.SubElement(
                        xml_feature, "attribute", attrib={"name": "image.burned_subtitles.locale"})
                    xml_feat_subs.text = settings.sub_feat

            else:
                xml_feat_text.text = "true"

            self.emit(QtCore.SIGNAL("feature_done"))

        # feature assets
        if settings.feature_assets:

            if not settings.feature:
                xml_assets = etree.SubElement(xml_root, "assets",
                                              attrib={"media_type": "video", "vendor_id": settings.vendor})
                xml_asset_feat = etree.SubElement(xml_assets, "asset", attrib={"type": "full"})

            def create_feat_assets(role, locale, asset_path, territories):
                xml_feat_data1 = etree.SubElement(xml_asset_feat, "data_file",
                                                  attrib={"role": role})

                if role != "notes":
                    xml_feat_data1_locale = etree.SubElement(xml_feat_data1, "locale",
                                                             attrib={"name": locale})
                xml_feat_data1_file = etree.SubElement(xml_feat_data1, "file_name")
                xml_feat_data1_file.text = os.path.basename(asset_path)
                xml_feat_data1_size = etree.SubElement(xml_feat_data1, "size")
                xml_feat_data1_size.text = str(os.path.getsize(asset_path))
                xml_feat_data1_md5 = etree.SubElement(xml_feat_data1, "checksum", attrib={"type": "md5"})
                xml_feat_data1_md5.text = hashfile(open(asset_path, 'rb'), hashlib.md5())

                if territories:
                    xml_feat_terr = etree.SubElement(xml_feat_data1, "territory_exclusions")

                    for terr in territories.values():
                        xml_feat_terr_exclude = etree.SubElement(xml_feat_terr, "territory")
                        xml_feat_terr_exclude.text = terr

            if settings.feat_asset1_path != "":
                create_feat_assets(
                    settings.feat_asset1_role, 
                    settings.feat_asset1_locale, 
                    settings.feat_asset1_path,
                    settings.feat_asset1_territories)

            if settings.feat_asset2_path != "":
                create_feat_assets(
                    settings.feat_asset2_role,
                    settings.feat_asset2_locale,
                    settings.feat_asset2_path,
                    settings.feat_asset2_territories)

            if settings.feat_asset3_path != "":
                create_feat_assets(
                    settings.feat_asset3_role,
                    settings.feat_asset3_locale,
                    settings.feat_asset3_path,
                    settings.feat_asset3_territories)

            if settings.feat_asset4_path != "":
                create_feat_assets(
                    settings.feat_asset4_role,
                    settings.feat_asset4_locale,
                    settings.feat_asset4_path,
                    settings.feat_asset4_territories)

            if settings.feat_asset5_path != "":
                create_feat_assets(
                    settings.feat_asset5_role,
                    settings.feat_asset5_locale,
                    settings.feat_asset5_path,
                    settings.feat_asset5_territories)

            if settings.feat_asset6_path != "":
                create_feat_assets(
                    settings.feat_asset6_role,
                    settings.feat_asset6_locale,
                    settings.feat_asset6_path,
                    settings.feat_asset6_territories)

            if settings.feat_asset7_path != "":
                create_feat_assets(
                    settings.feat_asset7_role,
                    settings.feat_asset7_locale,
                    settings.feat_asset7_path,
                    settings.feat_asset7_territories)

            if settings.feat_asset8_path != "":
                create_feat_assets(
                    settings.feat_asset8_role,
                    settings.feat_asset8_locale,
                    settings.feat_asset8_path,
                    settings.feat_asset8_territories)

            self.emit(QtCore.SIGNAL("feature_assets_done"))
                
        # chapters
        if settings.chapters and not settings.chapters_done:
            if (settings.feature or settings.feature_assets) and not settings.meta:
                xml_chapters = etree.SubElement(xml_asset_feat, "chapters")
                xml_tc = etree.SubElement(xml_chapters, "timecode_format")
                xml_tc.text = settings.timecodes.get(settings.tc_format)

            elif not settings.meta and not settings.feature and not settings.feature_assets:
                xml_video = etree.SubElement(xml_root, "video")
                xml_type = etree.SubElement(xml_video, "type")
                xml_type.text = "film"
                xml_subtype = etree.SubElement(xml_video, "subtype")
                xml_subtype.text = "feature"
                xml_vendor = etree.SubElement(xml_video, "vendor_id")
                xml_vendor.text = settings.vendor
                xml_chapters = etree.SubElement(xml_video, "chapters")
                xml_tc = etree.SubElement(xml_chapters, "timecode_format")
                xml_tc.text = settings.timecodes.get(settings.tc_format)

            def chapter_template(timecode, count, thumbnail):
                xml_chapter = etree.SubElement(xml_chapters, "chapter")
                xml_start = etree.SubElement(xml_chapter, "start_time")
                xml_start.text = timecode
                xml_chapter_titles = etree.SubElement(xml_chapter, "titles")

                def create_chapter_title(language):
                    xml_chapter_title = etree.SubElement(xml_chapter_titles, "title",
                                                         attrib={"locale": language})

                    if language[:2] == "af":
                        xml_chapter_title.text = u"Hoofstuk %s" % count
                    elif language[:2] == "ar":
                        xml_chapter_title.text = str(count) + u" باب"
                    elif language[:2] == "bg":
                        xml_chapter_title.text = u"Страница %s" % count
                    elif language[:2] == "ca":
                        xml_chapter_title.text = u"Capítol %s" % count
                    elif language[:8] == "cmn-Hans":
                        xml_chapter_title.text = u"章节 %s" % count
                    elif language[:8] == "cmn-Hant":
                        xml_chapter_title.text = u"章節 %s" % count
                    elif language[:2] == "cs":
                        xml_chapter_title.text = u"Kapitola %s" % count
                    elif language[:2] == "da" or language[:2] == "de" or language[:2] == "sv":
                        xml_chapter_title.text = u"Kapitel %s" % count
                    elif language[:2] == "el":
                        xml_chapter_title.text = u"Κεφάλαιο %s" % count
                    elif language[:2] == "es" or language[:2] == "pt":
                        xml_chapter_title.text = u"Capítulo %s" % count
                    elif language[:2] == "et":
                        xml_chapter_title.text = u"Peatükk %s" % count
                    elif language[:2] == "fi":
                        xml_chapter_title.text = u"Luku %s" % count
                    elif language[:2] == "fr":
                        xml_chapter_title.text = u"Chapitre %s" % count
                    elif language[:2] == "he":
                        xml_chapter_title.text = str(count) + u" פֶּרֶק"
                    elif language[:2] == "hi":
                        xml_chapter_title.text = u"अध्याय %s" % count
                    elif language[:2] == "hr":
                        xml_chapter_title.text = u"Poglavlje %s" % count
                    elif language[:2] == "hu":
                        xml_chapter_title.text = u"Fejezet %s" % count
                    elif language[:2] == "id" or language[:2] == "ms":
                        xml_chapter_title.text = u"Bab %s" % count
                    elif language[:2] == "is":
                        xml_chapter_title.text = u"Kafla %s" % count
                    elif language[:2] == "it":
                        xml_chapter_title.text = u"Capitolo %s" % count
                    elif language[:2] == "ja":
                        xml_chapter_title.text = u"チャプター %s" % count
                    elif language[:2] == "kk":
                        xml_chapter_title.text = u"Тарау %s" % count
                    elif language[:2] == "ko":
                        xml_chapter_title.text = u"장 %s" % count
                    elif language[:2] == "lb":
                        xml_chapter_title.text = u"Véiert %s" % count
                    elif language[:2] == "lo":
                        xml_chapter_title.text = u"ບົດ %s" % count
                    elif language[:2] == "lt":
                        xml_chapter_title.text = u"Skyrius %s" % count
                    elif language[:2] == "lv":
                        xml_chapter_title.text = u"Nodaļa %s" % count
                    elif language[:2] == "mt":
                        xml_chapter_title.text = u"Kapitolu %s" % count
                    elif language[:2] == "nl":
                        xml_chapter_title.text = u"Hoofdstuk %s" % count
                    elif language[:2] == "no":
                        xml_chapter_title.text = u"Kapittel %s" % count
                    elif language[:2] == "pl":
                        xml_chapter_title.text = u"Rozdział %s" % count
                    elif language[:2] == "ro":
                        xml_chapter_title.text = u"Capitol %s" % count
                    elif language[:2] == "ru":
                        xml_chapter_title.text = u"Глава %s" % count
                    elif language[:2] == "sk":
                        xml_chapter_title.text = u"Kapitola %s" % count
                    elif language[:2] == "sl":
                        xml_chapter_title.text = u"Poglavje %s" % count
                    elif language[:2] == "ta":
                        xml_chapter_title.text = u"அத்தியாயம் %s" % count
                    elif language[:2] == "te":
                        xml_chapter_title.text = u"అధ్యాయం %s" % count
                    elif language[:2] == "th":
                        xml_chapter_title.text = u"บท %s" % count
                    elif language[:2] == "tr":
                        xml_chapter_title.text = u"Bölüm %s" % count
                    elif language[:2] == "uk":
                        xml_chapter_title.text = u"Глава %s" % count
                    elif language[:2] == "ur":
                        xml_chapter_title.text = str(count) + u" باب"
                    elif language[:2] == "vi":
                        xml_chapter_title.text = u"Chương %s" % count
                    elif language[:2] == "zu":
                        xml_chapter_title.text = u"Isahluko %s" % count
                    else:
                        xml_chapter_title.text = u"Chapter %s" % count

                for value in settings.chapter_locales.values():
                    create_chapter_title(value.split(":", 1)[0])

                xml_chap_thumb = etree.SubElement(xml_chapter, "artwork_time")
                xml_chap_thumb.text = thumbnail

            chapter_number = 0
            for i in range(len(settings.chapters_tc.keys())):
                chapter_number += 1
                chapter_template(settings.chapters_tc.values()[i], chapter_number, settings.thumbs_tc.values()[i])

        settings.chapters_done = True
        self.emit(QtCore.SIGNAL("chapters_done"))

        if settings.trailer:
            if settings.feature or settings.feature_assets:
                xml_asset_trailer = etree.SubElement(xml_assets, "asset", attrib={"type": "preview"})

            else:
                if not settings.meta:
                    xml_assets = etree.SubElement(xml_root, "assets",
                                                  attrib={"media_type": "video", "vendor_id": settings.vendor})
                    xml_asset_trailer = etree.SubElement(xml_assets, "asset", attrib={"type": "preview"})

                elif settings.meta:
                    xml_assets = etree.SubElement(xml_video, "assets")
                    xml_asset_trailer = etree.SubElement(xml_assets, "asset", attrib={"type": "preview"})

            if settings.trailer_still != "":
                xml_trailer_thumb = etree.SubElement(
                    xml_asset_trailer,
                    "preview_image_time",
                    attrib={"format": settings.timecodes.get(settings.trailer_tc)})
                xml_trailer_thumb.text = settings.trailer_still

            xml_trailer_territories = etree.SubElement(xml_asset_trailer, "territories")
            xml_trailer_territory = etree.SubElement(xml_trailer_territories, "territory")
            xml_trailer_territory.text = "WW"
            xml_trailer = etree.SubElement(xml_asset_trailer, "data_file", attrib={"role": "source"})
            xml_trailer_locale = etree.SubElement(xml_trailer, "locale", attrib={"name": settings.trailer_audio})
            xml_trailer_file = etree.SubElement(xml_trailer, "file_name")
            xml_trailer_file.text = os.path.basename(settings.trailer_file_path)
            xml_trailer_size = etree.SubElement(xml_trailer, "size")
            xml_trailer_size.text = str(os.path.getsize(settings.trailer_file_path))
            xml_trailer_md5 = etree.SubElement(xml_trailer, "checksum",
                                               attrib={"type": "md5"})

            if settings.trailer_md5 == "":
                settings.trailer_md5 = hashfile(open(settings.trailer_file_path, 'rb'), hashlib.md5())
                xml_trailer_md5.text = settings.trailer_md5

            else:
                xml_trailer_md5.text = settings.trailer_md5

            xml_trailer_top = etree.SubElement(xml_trailer, "attribute", attrib={"name": "crop.top"})
            xml_trailer_top.text = settings.trailer_crop_top
            xml_trailer_bot = etree.SubElement(xml_trailer, "attribute", attrib={"name": "crop.bottom"})
            xml_trailer_bot.text = settings.trailer_crop_bottom
            xml_trailer_left = etree.SubElement(xml_trailer, "attribute", attrib={"name": "crop.left"})
            xml_trailer_left.text = settings.trailer_crop_left
            xml_trailer_right = etree.SubElement(xml_trailer, "attribute", attrib={"name": "crop.right"})
            xml_trailer_right.text = settings.trailer_crop_right
            xml_trailer_text = etree.SubElement(xml_trailer, "attribute", attrib={"name": "image.textless_master"})

            if settings.trailer_check_narr or settings.trailer_check_subs:
                xml_trailer_text.text = "false"

                if settings.trailer_check_narr:
                    xml_trailer_narr = etree.SubElement(
                        xml_trailer, "attribute", attrib={"name": "image.burned_forced_narrative.locale"})
                    xml_trailer_narr.text = settings.narr_trailer

                if settings.trailer_check_subs:
                    xml_trailer_subs = etree.SubElement(
                        xml_trailer, "attribute", attrib={"name": "image.burned_subtitles.locale"})
                    xml_trailer_subs.text = settings.sub_trailer

            else:
                xml_trailer_text.text = "true"

            self.emit(QtCore.SIGNAL("trailer_done"))

        # trailer assets
        if settings.trailer_assets:

            if not settings.feature and not settings.feature_assets and not settings.trailer:
                xml_assets = etree.SubElement(xml_root, "assets",
                                              attrib={"media_type": "video", "vendor_id": settings.vendor})
                xml_asset_trailer = etree.SubElement(xml_assets, "asset", attrib={"type": "preview"})

            elif (settings.feature or settings.feature_assets) and not settings.trailer:
                xml_asset_trailer = etree.SubElement(xml_assets, "asset", attrib={"type": "preview"})

            def create_trailer_assets(role, locale, asset_path):
                xml_trailer_data1 = etree.SubElement(xml_asset_trailer, "data_file",
                                                  attrib={"role": role})

                if role != "notes":
                    xml_trailer_data1_locale = etree.SubElement(xml_trailer_data1, "locale",
                                                             attrib={"name": locale})
                xml_trailer_data1_file = etree.SubElement(xml_trailer_data1, "file_name")
                xml_trailer_data1_file.text = os.path.basename(asset_path)
                xml_trailer_data1_size = etree.SubElement(xml_trailer_data1, "size")
                xml_trailer_data1_size.text = str(os.path.getsize(asset_path))
                xml_trailer_data1_md5 = etree.SubElement(xml_trailer_data1, "checksum", attrib={"type": "md5"})
                xml_trailer_data1_md5.text = hashfile(open(asset_path, 'rb'), hashlib.md5())

            if settings.trailer_asset1_path != "":
                create_trailer_assets(
                    settings.trailer_asset1_role,
                    settings.trailer_asset1_locale,
                    settings.trailer_asset1_path)

            if settings.trailer_asset2_path != "":
                create_trailer_assets(
                    settings.trailer_asset2_role,
                    settings.trailer_asset2_locale,
                    settings.trailer_asset2_path)

            if settings.trailer_asset3_path != "":
                create_trailer_assets(
                    settings.trailer_asset3_role,
                    settings.trailer_asset3_locale,
                    settings.trailer_asset3_path)

            if settings.trailer_asset4_path != "":
                create_trailer_assets(
                    settings.trailer_asset4_role,
                    settings.trailer_asset4_locale,
                    settings.trailer_asset4_path)

            if settings.trailer_asset5_path != "":
                create_trailer_assets(
                    settings.trailer_asset5_role,
                    settings.trailer_asset5_locale,
                    settings.trailer_asset5_path)

            if settings.trailer_asset6_path != "":
                create_trailer_assets(
                    settings.trailer_asset6_role,
                    settings.trailer_asset6_locale,
                    settings.trailer_asset6_path)

            if settings.trailer_asset7_path != "":
                create_trailer_assets(
                    settings.trailer_asset7_role,
                    settings.trailer_asset7_locale,
                    settings.trailer_asset7_path)

            if settings.trailer_asset8_path != "":
                create_trailer_assets(
                    settings.trailer_asset8_role,
                    settings.trailer_asset8_locale,
                    settings.trailer_asset8_path)

            self.emit(QtCore.SIGNAL("trailer_assets_done"))

        # localized trailer
        if settings.loc_trailer:
            if any([settings.feature, settings.feature_assets, settings.trailer, settings.trailer_assets]):
                xml_asset_loc_trailer = etree.SubElement(xml_assets, "asset", attrib={"type": "preview"})

            else:
                if not settings.meta:
                    xml_assets = etree.SubElement(xml_root, "assets",
                                                  attrib={"media_type": "video", "vendor_id": settings.vendor})
                    xml_asset_loc_trailer = etree.SubElement(xml_assets, "asset", attrib={"type": "preview"})

                elif settings.meta:
                    xml_assets = etree.SubElement(xml_video, "assets")
                    xml_asset_loc_trailer = etree.SubElement(xml_assets, "asset", attrib={"type": "preview"})

            if settings.loc_trailer_still != "":
                xml_loc_trailer_thumb = etree.SubElement(
                    xml_asset_loc_trailer,
                    "preview_image_time",
                    attrib={"format": settings.timecodes.get(settings.loc_trailer_tc)})
                xml_loc_trailer_thumb.text = settings.loc_trailer_still

            xml_loc_trailer_territories = etree.SubElement(xml_asset_loc_trailer, "territories")

            for terr in settings.loc_trailer_territories.values():
                xml_loc_trailer_territory = etree.SubElement(xml_loc_trailer_territories, "territory")
                xml_loc_trailer_territory.text = terr

            xml_loc_trailer = etree.SubElement(xml_asset_loc_trailer, "data_file", attrib={"role": "source"})
            xml_loc_trailer_locale = etree.SubElement(
                xml_loc_trailer, "locale", attrib={"name": settings.loc_trailer_audio})
            xml_loc_trailer_file = etree.SubElement(xml_loc_trailer, "file_name")
            xml_loc_trailer_file.text = os.path.basename(settings.loc_trailer_file_path)
            xml_loc_trailer_size = etree.SubElement(xml_loc_trailer, "size")
            xml_loc_trailer_size.text = str(os.path.getsize(settings.loc_trailer_file_path))
            xml_loc_trailer_md5 = etree.SubElement(xml_loc_trailer, "checksum",
                                               attrib={"type": "md5"})

            if settings.loc_trailer_md5 == "":
                settings.loc_trailer_md5 = hashfile(open(settings.loc_trailer_file_path, 'rb'), hashlib.md5())
                xml_loc_trailer_md5.text = settings.loc_trailer_md5

            else:
                xml_loc_trailer_md5.text = settings.loc_trailer_md5

            xml_loc_trailer_top = etree.SubElement(xml_loc_trailer, "attribute", attrib={"name": "crop.top"})
            xml_loc_trailer_top.text = settings.loc_trailer_crop_top
            xml_loc_trailer_bot = etree.SubElement(xml_loc_trailer, "attribute", attrib={"name": "crop.bottom"})
            xml_loc_trailer_bot.text = settings.loc_trailer_crop_bottom
            xml_loc_trailer_left = etree.SubElement(xml_loc_trailer, "attribute", attrib={"name": "crop.left"})
            xml_loc_trailer_left.text = settings.loc_trailer_crop_left
            xml_loc_trailer_right = etree.SubElement(xml_loc_trailer, "attribute", attrib={"name": "crop.right"})
            xml_loc_trailer_right.text = settings.loc_trailer_crop_right
            xml_loc_trailer_text = etree.SubElement(xml_loc_trailer, "attribute", attrib={"name": "image.textless_master"})

            if settings.loc_trailer_check_narr or settings.loc_trailer_check_subs:
                xml_loc_trailer_text.text = "false"

                if settings.loc_trailer_check_narr:
                    xml_loc_trailer_narr = etree.SubElement(
                        xml_loc_trailer, "attribute", attrib={"name": "image.burned_forced_narrative.locale"})
                    xml_loc_trailer_narr.text = settings.narr_loc_trailer

                if settings.loc_trailer_check_subs:
                    xml_loc_trailer_subs = etree.SubElement(
                        xml_loc_trailer, "attribute", attrib={"name": "image.burned_subtitles.locale"})
                    xml_loc_trailer_subs.text = settings.sub_trailer

            else:
                xml_loc_trailer_text.text = "true"

            self.emit(QtCore.SIGNAL("loc_trailer_done"))

        # localized trailer assets
        if settings.loc_trailer_assets:

            if not settings.feature \
                    and not settings.feature_assets \
                    and not settings.trailer \
                    and not settings.trailer_assets \
                    and not settings.loc_trailer:
                xml_assets = etree.SubElement(xml_root, "assets",
                                              attrib={"media_type": "video", "vendor_id": settings.vendor})
                xml_asset_loc_trailer = etree.SubElement(xml_assets, "asset", attrib={"type": "preview"})

            elif (settings.feature or settings.feature_assets or settings.trailer or settings.trailer_assets)\
                    and not settings.loc_trailer:
                xml_asset_loc_trailer = etree.SubElement(xml_assets, "asset", attrib={"type": "preview"})

            def create_trailer_assets(role, locale, asset_path):
                xml_loc_trailer_data1 = etree.SubElement(xml_asset_loc_trailer, "data_file",
                                                     attrib={"role": role})

                if role != "notes":
                    xml_loc_trailer_data1_locale = etree.SubElement(xml_loc_trailer_data1, "locale",
                                                                attrib={"name": locale})
                xml_loc_trailer_data1_file = etree.SubElement(xml_loc_trailer_data1, "file_name")
                xml_loc_trailer_data1_file.text = os.path.basename(asset_path)
                xml_loc_trailer_data1_size = etree.SubElement(xml_loc_trailer_data1, "size")
                xml_loc_trailer_data1_size.text = str(os.path.getsize(asset_path))
                xml_loc_trailer_data1_md5 = etree.SubElement(
                    xml_loc_trailer_data1, "checksum", attrib={"type": "md5"})
                xml_loc_trailer_data1_md5.text = hashfile(open(asset_path, 'rb'), hashlib.md5())

            if settings.loc_trailer_asset1_path != "":
                create_trailer_assets(
                    settings.loc_trailer_asset1_role,
                    settings.loc_trailer_asset1_locale,
                    settings.loc_trailer_asset1_path)

            if settings.loc_trailer_asset2_path != "":
                create_trailer_assets(
                    settings.loc_trailer_asset2_role,
                    settings.loc_trailer_asset2_locale,
                    settings.loc_trailer_asset2_path)

            if settings.loc_trailer_asset3_path != "":
                create_trailer_assets(
                    settings.loc_trailer_asset3_role,
                    settings.loc_trailer_asset3_locale,
                    settings.loc_trailer_asset3_path)

            if settings.loc_trailer_asset4_path != "":
                create_trailer_assets(
                    settings.loc_trailer_asset4_role,
                    settings.loc_trailer_asset4_locale,
                    settings.loc_trailer_asset4_path)

            if settings.loc_trailer_asset5_path != "":
                create_trailer_assets(
                    settings.loc_trailer_asset5_role,
                    settings.loc_trailer_asset5_locale,
                    settings.loc_trailer_asset5_path)

            if settings.loc_trailer_asset6_path != "":
                create_trailer_assets(
                    settings.loc_trailer_asset6_role,
                    settings.loc_trailer_asset6_locale,
                    settings.loc_trailer_asset6_path)

            if settings.loc_trailer_asset7_path != "":
                create_trailer_assets(
                    settings.loc_trailer_asset7_role,
                    settings.loc_trailer_asset7_locale,
                    settings.loc_trailer_asset7_path)

            if settings.loc_trailer_asset8_path != "":
                create_trailer_assets(
                    settings.loc_trailer_asset8_role,
                    settings.loc_trailer_asset8_locale,
                    settings.loc_trailer_asset8_path)

            self.emit(QtCore.SIGNAL("loc_trailer_assets_done"))

        # poster art
        if settings.poster:

            if any([
                settings.feature,
                settings.feature_assets,
                settings.trailer,
                settings.trailer_assets,
                settings.loc_trailer,
                settings.loc_trailer_assets
            ]):
                xml_artwork = etree.SubElement(xml_assets, "asset", attrib={"type": "artwork"})

            elif settings.meta \
                    and not settings.feature \
                    and not settings.feature_assets \
                    and not settings.trailer \
                    and not settings.trailer_assets \
                    and not settings.loc_trailer \
                    and not settings.loc_trailer_assets:
                xml_assets = etree.SubElement(xml_video, "assets")
                xml_artwork = etree.SubElement(xml_assets, "asset", attrib={"type": "artwork"})

            else:
                xml_assets = etree.SubElement(xml_root, "assets",
                                              attrib={"media_type": "video", "vendor_id": settings.vendor})
                xml_artwork = etree.SubElement(xml_assets, "asset", attrib={"type": "artwork"})

            xml_poster_territories = etree.SubElement(xml_artwork, "territories")
            xml_poster_territory = etree.SubElement(xml_poster_territories, "territory")
            xml_poster_territory.text = "WW"
            xml_poster_data = etree.SubElement(xml_artwork, "data_file")
            xml_poster_locale = etree.SubElement(xml_poster_data, "locale",
                                                 attrib={"name": settings.poster_locale})
            xml_poster_file = etree.SubElement(xml_poster_data, "file_name")
            xml_poster_file.text = os.path.basename(settings.poster_file_path)
            xml_poster_md5 = etree.SubElement(xml_poster_data, "checksum", attrib={"type": "md5"})
            xml_poster_md5.text = hashfile(open(settings.poster_file_path, 'rb'), hashlib.md5())
            xml_poster_size = etree.SubElement(xml_poster_data, "size")
            xml_poster_size.text = str(os.path.getsize(settings.poster_file_path))

            self.emit(QtCore.SIGNAL("poster_done"))

        if not settings.meta and (settings.feature or settings.feature_assets):
            # accessibility info
            xml_access_info = etree.SubElement(xml_video, "accessibility_info")

            if settings.feat_asset1_role == "captions" \
                    or settings.feat_asset2_role == "captions" \
                    or settings.feat_asset3_role == "captions" \
                    or settings.feat_asset3_role == "captions" \
                    or settings.feat_asset4_role == "captions" \
                    or settings.feat_asset5_role == "captions" \
                    or settings.feat_asset6_role == "captions" \
                    or settings.feat_asset7_role == "captions" \
                    or settings.feat_asset8_role == "captions":
                xml_access = etree.SubElement(
                    xml_access_info,
                    "accessibility",
                    attrib={"role": "captions", "available": "true"})

            else:
                xml_access = etree.SubElement(
                    xml_access_info,
                    "accessibility",
                    attrib={
                        "role": "captions",
                        "available": "false",
                        "reason_code": "NO_CC_SDH_FOREIGN_LANGUAGE_ENGLISH_SUBS"})

        # product info
        if settings.product:
            xml_products = etree.SubElement(xml_video, "products")

            def create_product(
                    territory,
                    cleared_sales,
                    price_sd_check,
                    price_hd_check,
                    sd_price,
                    hd_price,
                    sales_start_check,
                    sales_start,
                    sales_end_check,
                    sales_end,
                    preorder_check,
                    preorder,
                    cleared_vod,
                    vod_type_check,
                    vod_type,
                    vod_start_check,
                    vod_start,
                    vod_end_check,
                    vod_end,
                    physical_check,
                    physical):
                xml_product1 = etree.SubElement(xml_products, "product")
                xml_territory1 = etree.SubElement(xml_product1, "territory")
                xml_territory1.text = territory
                xml_cleared_sale_sd = etree.SubElement(xml_product1, "cleared_for_sale")
                xml_cleared_sale_sd.text = cleared_sales
                xml_cleared_sale_hd = etree.SubElement(xml_product1, "cleared_for_hd_sale")
                xml_cleared_sale_hd.text = cleared_sales

                if price_sd_check:
                    xml_sd_price = etree.SubElement(xml_product1, "wholesale_price_tier")
                    xml_sd_price.text = sd_price

                if price_hd_check:
                    xml_hd_price = etree.SubElement(xml_product1, "hd_wholesale_price_tier")
                    xml_hd_price.text = hd_price

                if sales_start_check:
                    xml_sales_start = etree.SubElement(xml_product1, "sales_start_date")
                    xml_sales_start.text = sales_start

                if sales_end_check:
                    xml_sales_end = etree.SubElement(xml_product1, "sales_end_date")
                    xml_sales_end.text = sales_end

                if preorder_check:
                    xml_preorder = etree.SubElement(xml_product1, "preorder_sales_start_date")
                    xml_preorder.text = preorder

                xml_cleared_vod = etree.SubElement(xml_product1, "cleared_for_vod")
                xml_cleared_vod.text = cleared_vod
                xml_cleared_hd_vod = etree.SubElement(xml_product1, "cleared_for_hd_vod")
                xml_cleared_hd_vod.text = cleared_vod

                if vod_type_check:
                    xml_vod_type = etree.SubElement(xml_product1, "vod_type")
                    xml_vod_type.text = vod_type

                if vod_start_check:
                    xml_vod_start = etree.SubElement(xml_product1, "available_for_vod_date")
                    xml_vod_start.text = vod_start

                if vod_end_check:
                    xml_vod_end = etree.SubElement(xml_product1, "unavailable_for_vod_date")
                    xml_vod_end.text = vod_end

                if physical_check:
                    xml_physical = etree.SubElement(xml_product1, "physical_release_date")
                    xml_physical.text = physical

            if settings.product1_check:
                create_product(
                    settings.product1_terr,
                    settings.product1_sale_clear,
                    settings.product1_price_sd_check,
                    settings.product1_price_hd_check,
                    settings.product1_price_sd,
                    settings.product1_price_hd,
                    settings.product1_sales_start_check,
                    settings.product1_sales_start,
                    settings.product1_sales_end_check,
                    settings.product1_sales_end,
                    settings.product1_preorder_check,
                    settings.product1_preorder,
                    settings.product1_vod_clear,
                    settings.product1_vod_type_check,
                    settings.product1_vod_type,
                    settings.product1_vod_start_check,
                    settings.product1_vod_start,
                    settings.product1_vod_end_check,
                    settings.product1_vod_end,
                    settings.product1_physical_check,
                    settings.product1_physical
                )

            if settings.product2_check:
                create_product(
                    settings.product2_terr,
                    settings.product2_sale_clear,
                    settings.product2_price_sd_check,
                    settings.product2_price_hd_check,
                    settings.product2_price_sd,
                    settings.product2_price_hd,
                    settings.product2_sales_start_check,
                    settings.product2_sales_start,
                    settings.product2_sales_end_check,
                    settings.product2_sales_end,
                    settings.product2_preorder_check,
                    settings.product2_preorder,
                    settings.product2_vod_clear,
                    settings.product2_vod_type_check,
                    settings.product2_vod_type,
                    settings.product2_vod_start_check,
                    settings.product2_vod_start,
                    settings.product2_vod_end_check,
                    settings.product2_vod_end,
                    settings.product2_physical_check,
                    settings.product2_physical
                )

            if settings.product3_check:
                create_product(
                    settings.product3_terr,
                    settings.product3_sale_clear,
                    settings.product3_price_sd_check,
                    settings.product3_price_hd_check,
                    settings.product3_price_sd,
                    settings.product3_price_hd,
                    settings.product3_sales_start_check,
                    settings.product3_sales_start,
                    settings.product3_sales_end_check,
                    settings.product3_sales_end,
                    settings.product3_preorder_check,
                    settings.product3_preorder,
                    settings.product3_vod_clear,
                    settings.product3_vod_type_check,
                    settings.product3_vod_type,
                    settings.product3_vod_start_check,
                    settings.product3_vod_start,
                    settings.product3_vod_end_check,
                    settings.product3_vod_end,
                    settings.product3_physical_check,
                    settings.product3_physical
                )

            if settings.product4_check:
                create_product(
                    settings.product4_terr,
                    settings.product4_sale_clear,
                    settings.product4_price_sd_check,
                    settings.product4_price_hd_check,
                    settings.product4_price_sd,
                    settings.product4_price_hd,
                    settings.product4_sales_start_check,
                    settings.product4_sales_start,
                    settings.product4_sales_end_check,
                    settings.product4_sales_end,
                    settings.product4_preorder_check,
                    settings.product4_preorder,
                    settings.product4_vod_clear,
                    settings.product4_vod_type_check,
                    settings.product4_vod_type,
                    settings.product4_vod_start_check,
                    settings.product4_vod_start,
                    settings.product4_vod_end_check,
                    settings.product4_vod_end,
                    settings.product4_physical_check,
                    settings.product4_physical
                )

            self.emit(QtCore.SIGNAL("product_done"))

        # creates the xml file
        tree = etree.ElementTree(xml_root)
        tree.write("metadata.xml",
                   xml_declaration=True,
                   encoding="UTF-8",
                   pretty_print=True)

        # validates the xml
        relaxng = etree.RelaxNG(settings.relaxng_doc)
        validation = etree.parse("metadata.xml")
        if not relaxng.validate(validation):
            settings.results = str(relaxng.error_log)

        else:
            settings.results = "Validation successful."


class AboutDlg(QtGui.QDialog, about_dlg.Ui_About):
    def __init__(self, parent=None):
        super(AboutDlg, self).__init__(parent)

        self.setupUi(self)


class XmlGeneratorApp(QtGui.QMainWindow, main_frame.Ui_XmlGenUI):
    def __init__(self, parent=None):
        super(XmlGeneratorApp, self).__init__(parent)

        self.feat_md5_thread = FeatureMd5()
        self.trailer_md5_thread = TrailerMd5()
        self.loc_trailer_md5_thread = LocTrailerMd5()
        self.create_xml_thread = CreateXml()
        self.chapter_pixmap = ""

        read_rng()
        create_providers()
        create_countries()
        list_of_countries = create_list("country_lst", settings.countries)
        self.list_of_languages = create_list("language_lst", languages_list.languages)

        self.loc_trailer_count = 0
        self.feat_asset1_count = 0
        self.feat_asset2_count = 0
        self.feat_asset3_count = 0
        self.feat_asset4_count = 0
        self.feat_asset5_count = 0
        self.feat_asset6_count = 0
        self.feat_asset7_count = 0
        self.feat_asset8_count = 0
        self.chapter_locale_count = 0
        self.country_values = settings.countries.values()
        self.country_values.sort()

        self.setupUi(self)

        # menubar
        self.actionAbout.triggered.connect(self.about_dlg)
        self.actionQuit_4.triggered.connect(self.quit_fcn)

        # metadata
        self.comboCountry.clear()
        self.comboCountry.addItems(list_of_countries)
        self.comboCountry.currentIndexChanged.connect(self.set_country)
        index_country = self.comboCountry.findText("UNITED STATES: US", QtCore.Qt.MatchFixedString)
        self.comboCountry.setCurrentIndex(index_country)

        self.comboOriginalLanguage.clear()
        self.comboOriginalLanguage.addItems(self.list_of_languages)
        self.comboOriginalLanguage.currentIndexChanged.connect(self.set_spoken)
        index_original_locale = self.comboOriginalLanguage.findText("en-US: English (United States)", QtCore.Qt.MatchFixedString)
        self.comboOriginalLanguage.setCurrentIndex(index_original_locale)

        self.adapted_title.textChanged.connect(self.set_title)
        self.release_title.textChanged.connect(self.set_title_studio)
        self.synopsis.textChanged.connect(self.set_synopsis)
        self.production.textChanged.connect(self.set_company)
        self.copyright.textChanged.connect(self.set_cline)
        self.theatrical.textChanged.connect(self.set_theatrical)

        # genres and ratings
        genres_lst = genres.genres.keys()
        genres_lst.sort()

        self.genre1.clear()
        self.genre1.addItems(genres_lst)
        self.genre1.currentIndexChanged.connect(self.set_genre1)

        self.genre2.clear()
        self.genre2.addItems(genres_lst)
        self.genre2.currentIndexChanged.connect(self.set_genre2)

        self.genre3.clear()
        self.genre3.addItems(genres_lst)
        self.genre3.currentIndexChanged.connect(self.set_genre3)

        self.genre4.clear()
        self.genre4.addItems(genres_lst)
        self.genre4.currentIndexChanged.connect(self.set_genre4)

        self.genre5.clear()
        self.genre5.addItems(genres_lst)
        self.genre5.currentIndexChanged.connect(self.set_genre5)

        self.genre6.clear()
        self.genre6.addItems(genres_lst)
        self.genre6.currentIndexChanged.connect(self.set_genre6)

        self.genre7.clear()
        self.genre7.addItems(genres_lst)
        self.genre7.currentIndexChanged.connect(self.set_genre7)

        self.genre8.clear()
        self.genre8.addItems(genres_lst)
        self.genre8.currentIndexChanged.connect(self.set_genre8)

        # ratings
        ratings_sys_values = ratings.systems.values()
        ratings_sys_values.sort()
        
        self.rating1_sys.clear()
        self.rating1_sys.addItems(ratings_sys_values)
        self.rating1_sys.currentIndexChanged.connect(self.set_rating1_sys)

        self.rating2_sys.clear()
        self.rating2_sys.addItems(ratings_sys_values)
        self.rating2_sys.currentIndexChanged.connect(self.set_rating2_sys)

        self.rating3_sys.clear()
        self.rating3_sys.addItems(ratings_sys_values)
        self.rating3_sys.currentIndexChanged.connect(self.set_rating3_sys)

        self.rating4_sys.clear()
        self.rating4_sys.addItems(ratings_sys_values)
        self.rating4_sys.currentIndexChanged.connect(self.set_rating4_sys)

        self.rating5_sys.clear()
        self.rating5_sys.addItems(ratings_sys_values)
        self.rating5_sys.currentIndexChanged.connect(self.set_rating5_sys)

        self.rating1_value.textChanged.connect(self.set_rating1_value)
        self.rating2_value.textChanged.connect(self.set_rating2_value)
        self.rating3_value.textChanged.connect(self.set_rating3_value)
        self.rating4_value.textChanged.connect(self.set_rating4_value)
        self.rating5_value.textChanged.connect(self.set_rating5_value)

        # cast
        self.actor1_name.textChanged.connect(self.set_actor1_name)
        self.actor2_name.textChanged.connect(self.set_actor2_name)
        self.actor3_name.textChanged.connect(self.set_actor3_name)
        self.actor4_name.textChanged.connect(self.set_actor4_name)
        self.actor5_name.textChanged.connect(self.set_actor5_name)
        self.actor6_name.textChanged.connect(self.set_actor6_name)
        self.actor7_name.textChanged.connect(self.set_actor7_name)
        self.actor8_name.textChanged.connect(self.set_actor8_name)
        self.actor9_name.textChanged.connect(self.set_actor9_name)
        self.actor10_name.textChanged.connect(self.set_actor10_name)

        self.actor1_apple_id.textChanged.connect(self.set_actor1_apple_id)
        self.actor2_apple_id.textChanged.connect(self.set_actor2_apple_id)
        self.actor3_apple_id.textChanged.connect(self.set_actor3_apple_id)
        self.actor4_apple_id.textChanged.connect(self.set_actor4_apple_id)
        self.actor5_apple_id.textChanged.connect(self.set_actor5_apple_id)
        self.actor6_apple_id.textChanged.connect(self.set_actor6_apple_id)
        self.actor7_apple_id.textChanged.connect(self.set_actor7_apple_id)
        self.actor8_apple_id.textChanged.connect(self.set_actor8_apple_id)
        self.actor9_apple_id.textChanged.connect(self.set_actor9_apple_id)
        self.actor10_apple_id.textChanged.connect(self.set_actor10_apple_id)

        self.actor1_char.textChanged.connect(self.set_actor1_char)
        self.actor2_char.textChanged.connect(self.set_actor2_char)
        self.actor3_char.textChanged.connect(self.set_actor3_char)
        self.actor4_char.textChanged.connect(self.set_actor4_char)
        self.actor5_char.textChanged.connect(self.set_actor5_char)
        self.actor6_char.textChanged.connect(self.set_actor6_char)
        self.actor7_char.textChanged.connect(self.set_actor7_char)
        self.actor8_char.textChanged.connect(self.set_actor8_char)
        self.actor9_char.textChanged.connect(self.set_actor9_char)
        self.actor10_char.textChanged.connect(self.set_actor10_char)

        self.actor1_char2.textChanged.connect(self.set_actor1_char2)
        self.actor2_char2.textChanged.connect(self.set_actor2_char2)
        self.actor3_char2.textChanged.connect(self.set_actor3_char2)
        self.actor4_char2.textChanged.connect(self.set_actor4_char2)
        self.actor5_char2.textChanged.connect(self.set_actor5_char2)
        self.actor6_char2.textChanged.connect(self.set_actor6_char2)
        self.actor7_char2.textChanged.connect(self.set_actor7_char2)
        self.actor8_char2.textChanged.connect(self.set_actor8_char2)
        self.actor9_char2.textChanged.connect(self.set_actor9_char2)
        self.actor10_char2.textChanged.connect(self.set_actor10_char2)

        self.actor1_ref.textChanged.connect(self.set_actor1_ref)
        self.actor2_ref.textChanged.connect(self.set_actor2_ref)
        self.actor3_ref.textChanged.connect(self.set_actor3_ref)
        self.actor4_ref.textChanged.connect(self.set_actor4_ref)
        self.actor5_ref.textChanged.connect(self.set_actor5_ref)
        self.actor6_ref.textChanged.connect(self.set_actor6_ref)
        self.actor7_ref.textChanged.connect(self.set_actor7_ref)
        self.actor8_ref.textChanged.connect(self.set_actor8_ref)
        self.actor9_ref.textChanged.connect(self.set_actor9_ref)
        self.actor10_ref.textChanged.connect(self.set_actor10_ref)

        self.actor1_ref2.textChanged.connect(self.set_actor1_ref2)
        self.actor2_ref2.textChanged.connect(self.set_actor2_ref2)
        self.actor3_ref2.textChanged.connect(self.set_actor3_ref2)
        self.actor4_ref2.textChanged.connect(self.set_actor4_ref2)
        self.actor5_ref2.textChanged.connect(self.set_actor5_ref2)
        self.actor6_ref2.textChanged.connect(self.set_actor6_ref2)
        self.actor7_ref2.textChanged.connect(self.set_actor7_ref2)
        self.actor8_ref2.textChanged.connect(self.set_actor8_ref2)
        self.actor9_ref2.textChanged.connect(self.set_actor9_ref2)
        self.actor10_ref2.textChanged.connect(self.set_actor10_ref2)

        # crew
        self.crew1_name.textChanged.connect(self.set_crew1_name)
        self.crew2_name.textChanged.connect(self.set_crew2_name)
        self.crew3_name.textChanged.connect(self.set_crew3_name)
        self.crew4_name.textChanged.connect(self.set_crew4_name)
        self.crew5_name.textChanged.connect(self.set_crew5_name)
        self.crew6_name.textChanged.connect(self.set_crew6_name)
        self.crew7_name.textChanged.connect(self.set_crew7_name)
        self.crew8_name.textChanged.connect(self.set_crew8_name)
        self.crew9_name.textChanged.connect(self.set_crew9_name)
        self.crew10_name.textChanged.connect(self.set_crew10_name)

        self.crew1_apple_id.textChanged.connect(self.set_crew1_apple_id)
        self.crew2_apple_id.textChanged.connect(self.set_crew2_apple_id)
        self.crew3_apple_id.textChanged.connect(self.set_crew3_apple_id)
        self.crew4_apple_id.textChanged.connect(self.set_crew4_apple_id)
        self.crew5_apple_id.textChanged.connect(self.set_crew5_apple_id)
        self.crew6_apple_id.textChanged.connect(self.set_crew6_apple_id)
        self.crew7_apple_id.textChanged.connect(self.set_crew7_apple_id)
        self.crew8_apple_id.textChanged.connect(self.set_crew8_apple_id)
        self.crew9_apple_id.textChanged.connect(self.set_crew9_apple_id)
        self.crew10_apple_id.textChanged.connect(self.set_crew10_apple_id)

        self.crew1_director.stateChanged.connect(self.set_crew1_director)
        self.crew1_producer.stateChanged.connect(self.set_crew1_producer)
        self.crew1_screenwriter.stateChanged.connect(self.set_crew1_screenwriter)
        self.crew1_composer.stateChanged.connect(self.set_crew1_composer)
        self.crew1_codirector.stateChanged.connect(self.set_crew1_codirector)

        self.crew2_director.stateChanged.connect(self.set_crew2_director)
        self.crew2_producer.stateChanged.connect(self.set_crew2_producer)
        self.crew2_screenwriter.stateChanged.connect(self.set_crew2_screenwriter)
        self.crew2_composer.stateChanged.connect(self.set_crew2_composer)
        self.crew2_codirector.stateChanged.connect(self.set_crew2_codirector)

        self.crew3_director.stateChanged.connect(self.set_crew3_director)
        self.crew3_producer.stateChanged.connect(self.set_crew3_producer)
        self.crew3_screenwriter.stateChanged.connect(self.set_crew3_screenwriter)
        self.crew3_composer.stateChanged.connect(self.set_crew3_composer)
        self.crew3_codirector.stateChanged.connect(self.set_crew3_codirector)

        self.crew4_director.stateChanged.connect(self.set_crew4_director)
        self.crew4_producer.stateChanged.connect(self.set_crew4_producer)
        self.crew4_screenwriter.stateChanged.connect(self.set_crew4_screenwriter)
        self.crew4_composer.stateChanged.connect(self.set_crew4_composer)
        self.crew4_codirector.stateChanged.connect(self.set_crew4_codirector)

        self.crew5_director.stateChanged.connect(self.set_crew5_director)
        self.crew5_producer.stateChanged.connect(self.set_crew5_producer)
        self.crew5_screenwriter.stateChanged.connect(self.set_crew5_screenwriter)
        self.crew5_composer.stateChanged.connect(self.set_crew5_composer)
        self.crew5_codirector.stateChanged.connect(self.set_crew5_codirector)

        self.crew6_director.stateChanged.connect(self.set_crew6_director)
        self.crew6_producer.stateChanged.connect(self.set_crew6_producer)
        self.crew6_screenwriter.stateChanged.connect(self.set_crew6_screenwriter)
        self.crew6_composer.stateChanged.connect(self.set_crew6_composer)
        self.crew6_codirector.stateChanged.connect(self.set_crew6_codirector)

        self.crew7_director.stateChanged.connect(self.set_crew7_director)
        self.crew7_producer.stateChanged.connect(self.set_crew7_producer)
        self.crew7_screenwriter.stateChanged.connect(self.set_crew7_screenwriter)
        self.crew7_composer.stateChanged.connect(self.set_crew7_composer)
        self.crew7_codirector.stateChanged.connect(self.set_crew7_codirector)

        self.crew8_director.stateChanged.connect(self.set_crew8_director)
        self.crew8_producer.stateChanged.connect(self.set_crew8_producer)
        self.crew8_screenwriter.stateChanged.connect(self.set_crew8_screenwriter)
        self.crew8_composer.stateChanged.connect(self.set_crew8_composer)
        self.crew8_codirector.stateChanged.connect(self.set_crew8_codirector)

        self.crew9_director.stateChanged.connect(self.set_crew9_director)
        self.crew9_producer.stateChanged.connect(self.set_crew9_producer)
        self.crew9_screenwriter.stateChanged.connect(self.set_crew9_screenwriter)
        self.crew9_composer.stateChanged.connect(self.set_crew9_composer)
        self.crew9_codirector.stateChanged.connect(self.set_crew9_codirector)

        self.crew10_director.stateChanged.connect(self.set_crew10_director)
        self.crew10_producer.stateChanged.connect(self.set_crew10_producer)
        self.crew10_screenwriter.stateChanged.connect(self.set_crew10_screenwriter)
        self.crew10_composer.stateChanged.connect(self.set_crew10_composer)
        self.crew10_codirector.stateChanged.connect(self.set_crew10_codirector)

        # feature
        self.comboFeatureAudio.clear()
        self.comboFeatureAudio.addItems(self.list_of_languages)
        self.comboFeatureAudio.currentIndexChanged.connect(self.set_feat_audio)
        index_feature_audio = self.comboFeatureAudio.findText("en-US: English (United States)", QtCore.Qt.MatchFixedString)
        self.comboFeatureAudio.setCurrentIndex(index_feature_audio)

        self.comboNarrFeature.clear()
        self.comboNarrFeature.addItems(self.list_of_languages)
        self.comboNarrFeature.currentIndexChanged.connect(self.set_narr_feat)
        index_feature_narr = self.comboNarrFeature.findText("en-US: English (United States)", QtCore.Qt.MatchFixedString)
        self.comboNarrFeature.setCurrentIndex(index_feature_narr)

        self.comboSubFeature.clear()
        self.comboSubFeature.addItems(self.list_of_languages)
        self.comboSubFeature.currentIndexChanged.connect(self.set_sub_feat)
        index_feature_subs = self.comboSubFeature.findText("en-US: English (United States)", QtCore.Qt.MatchFixedString)
        self.comboSubFeature.setCurrentIndex(index_feature_subs)

        self.feat_top_crop.textChanged.connect(self.set_feat_top_crop)
        self.feat_bottom_crop.textChanged.connect(self.set_feat_bottom_crop)
        self.feat_left_crop.textChanged.connect(self.set_feat_left_crop)
        self.feat_right_crop.textChanged.connect(self.set_feat_right_crop)

        self.feature_file.clicked.connect(self.feature_file_dlg)
        self.feat_md5_start_btn.clicked.connect(self.feature_md5_start)
        self.feat_md5_stop_btn.clicked.connect(self.feature_md5_stop)
        self.feat_md5_lbl.textChanged.connect(self.set_feat_md5_lbl)

        self.feat_narratives.stateChanged.connect(self.check_feat_narr)
        self.feat_subs.stateChanged.connect(self.check_feat_subs)

        # chapters
        tc_lst = settings.timecodes.keys()
        tc_lst.sort()
        self.tc_format.clear()
        self.tc_format.addItems(tc_lst)
        self.tc_format.currentIndexChanged.connect(self.set_timecode_format)
        index_tc_format = self.tc_format.findText("23.98fps", QtCore.Qt.MatchFixedString)
        self.tc_format.setCurrentIndex(index_tc_format)

        self.chapter_locale_cb_main.clear()
        self.chapter_locale_cb_main.addItems(self.list_of_languages)
        self.chapter_locale_cb_main.currentIndexChanged.connect(self.set_chapter_locales)

        self.chapter_locale_add_btn.clicked.connect(self.chap_locale_add)
        self.chapter_locale_del_btn.clicked.connect(self.chap_locale_del)

        self.chap_01_tc_ln.textChanged.connect(self.set_chap_01_tc)
        self.chap_02_tc_ln.textChanged.connect(self.set_chap_02_tc)
        self.chap_03_tc_ln.textChanged.connect(self.set_chap_03_tc)
        self.chap_04_tc_ln.textChanged.connect(self.set_chap_04_tc)
        self.chap_05_tc_ln.textChanged.connect(self.set_chap_05_tc)
        self.chap_06_tc_ln.textChanged.connect(self.set_chap_06_tc)
        self.chap_07_tc_ln.textChanged.connect(self.set_chap_07_tc)
        self.chap_08_tc_ln.textChanged.connect(self.set_chap_08_tc)
        self.chap_09_tc_ln.textChanged.connect(self.set_chap_09_tc)
        self.chap_10_tc_ln.textChanged.connect(self.set_chap_10_tc)
        self.chap_11_tc_ln.textChanged.connect(self.set_chap_11_tc)
        self.chap_12_tc_ln.textChanged.connect(self.set_chap_12_tc)
        self.chap_13_tc_ln.textChanged.connect(self.set_chap_13_tc)
        self.chap_14_tc_ln.textChanged.connect(self.set_chap_14_tc)
        self.chap_15_tc_ln.textChanged.connect(self.set_chap_15_tc)
        self.chap_16_tc_ln.textChanged.connect(self.set_chap_16_tc)
        self.chap_17_tc_ln.textChanged.connect(self.set_chap_17_tc)
        self.chap_18_tc_ln.textChanged.connect(self.set_chap_18_tc)
        self.chap_19_tc_ln.textChanged.connect(self.set_chap_19_tc)
        self.chap_20_tc_ln.textChanged.connect(self.set_chap_20_tc)

        self.chap_01_thumb_tc_ln.textChanged.connect(self.set_chap_01_thumb_tc)
        self.chap_02_thumb_tc_ln.textChanged.connect(self.set_chap_02_thumb_tc)
        self.chap_03_thumb_tc_ln.textChanged.connect(self.set_chap_03_thumb_tc)
        self.chap_04_thumb_tc_ln.textChanged.connect(self.set_chap_04_thumb_tc)
        self.chap_05_thumb_tc_ln.textChanged.connect(self.set_chap_05_thumb_tc)
        self.chap_06_thumb_tc_ln.textChanged.connect(self.set_chap_06_thumb_tc)
        self.chap_07_thumb_tc_ln.textChanged.connect(self.set_chap_07_thumb_tc)
        self.chap_08_thumb_tc_ln.textChanged.connect(self.set_chap_08_thumb_tc)
        self.chap_09_thumb_tc_ln.textChanged.connect(self.set_chap_09_thumb_tc)
        self.chap_10_thumb_tc_ln.textChanged.connect(self.set_chap_10_thumb_tc)
        self.chap_11_thumb_tc_ln.textChanged.connect(self.set_chap_11_thumb_tc)
        self.chap_12_thumb_tc_ln.textChanged.connect(self.set_chap_12_thumb_tc)
        self.chap_13_thumb_tc_ln.textChanged.connect(self.set_chap_13_thumb_tc)
        self.chap_14_thumb_tc_ln.textChanged.connect(self.set_chap_14_thumb_tc)
        self.chap_15_thumb_tc_ln.textChanged.connect(self.set_chap_15_thumb_tc)
        self.chap_16_thumb_tc_ln.textChanged.connect(self.set_chap_16_thumb_tc)
        self.chap_17_thumb_tc_ln.textChanged.connect(self.set_chap_17_thumb_tc)
        self.chap_18_thumb_tc_ln.textChanged.connect(self.set_chap_18_thumb_tc)
        self.chap_19_thumb_tc_ln.textChanged.connect(self.set_chap_19_thumb_tc)
        self.chap_20_thumb_tc_ln.textChanged.connect(self.set_chap_20_thumb_tc)

        # trailer
        tc_lst = settings.timecodes.keys()
        tc_lst.sort()
        self.tc_format_ww_trailer.clear()
        self.tc_format_ww_trailer.addItems(tc_lst)
        self.tc_format_ww_trailer.currentIndexChanged.connect(self.set_trailer_tc_format)
        index_tc_format_ww = self.tc_format_ww_trailer.findText("23.98fps", QtCore.Qt.MatchFixedString)
        self.tc_format_ww_trailer.setCurrentIndex(index_tc_format_ww)

        self.comboTrailerAudio.clear()
        self.comboTrailerAudio.addItems(self.list_of_languages)
        self.comboTrailerAudio.currentIndexChanged.connect(self.set_trailer_audio)
        index_trailer_audio = self.comboTrailerAudio.findText("en-US: English (United States)", QtCore.Qt.MatchFixedString)
        self.comboTrailerAudio.setCurrentIndex(index_trailer_audio)

        self.comboNarrTrailer.clear()
        self.comboNarrTrailer.addItems(self.list_of_languages)
        self.comboNarrTrailer.currentIndexChanged.connect(self.set_narr_trailer)
        index_trailer_narr = self.comboNarrTrailer.findText("en-US: English (United States)", QtCore.Qt.MatchFixedString)
        self.comboNarrTrailer.setCurrentIndex(index_trailer_narr)

        self.comboSubTrailer.clear()
        self.comboSubTrailer.addItems(self.list_of_languages)
        self.comboSubTrailer.currentIndexChanged.connect(self.set_sub_trailer)
        index_trailer_subs = self.comboSubTrailer.findText("en-US: English (United States)", QtCore.Qt.MatchFixedString)
        self.comboSubTrailer.setCurrentIndex(index_trailer_subs)

        self.trailer_still_tc.textChanged.connect(self.set_trailer_still_tc)

        self.trailer_top_crop.textChanged.connect(self.set_trailer_top_crop)
        self.trailer_bottom_crop.textChanged.connect(self.set_trailer_bottom_crop)
        self.trailer_left_crop.textChanged.connect(self.set_trailer_left_crop)
        self.trailer_right_crop.textChanged.connect(self.set_trailer_right_crop)

        self.trailer_file.clicked.connect(self.trailer_file_dlg)
        self.trailer_md5_start_btn.clicked.connect(self.trailer_md5_start)
        self.trailer_md5_stop_btn.clicked.connect(self.trailer_md5_stop)
        self.trailer_md5_lbl.textChanged.connect(self.set_trailer_md5_lbl)

        self.trailer_narr.stateChanged.connect(self.check_trailer_narr)
        self.trailer_subs.stateChanged.connect(self.check_trailer_subs)

        # feature assets
        self.feat_asset1_btn.clicked.connect(self.feat_asset1_dlg)
        self.feat_asset2_btn.clicked.connect(self.feat_asset2_dlg)
        self.feat_asset3_btn.clicked.connect(self.feat_asset3_dlg)
        self.feat_asset4_btn.clicked.connect(self.feat_asset4_dlg)
        self.feat_asset5_btn.clicked.connect(self.feat_asset5_dlg)
        self.feat_asset6_btn.clicked.connect(self.feat_asset6_dlg)
        self.feat_asset7_btn.clicked.connect(self.feat_asset7_dlg)
        self.feat_asset8_btn.clicked.connect(self.feat_asset8_dlg)

        self.feat_asset1_role.clear()
        self.feat_asset1_role.addItems(settings.data_roles)
        self.feat_asset1_role.currentIndexChanged.connect(self.set_feat_asset1_role)

        self.feat_asset1_locale.clear()
        self.feat_asset1_locale.addItems(self.list_of_languages)
        self.feat_asset1_locale.currentIndexChanged.connect(self.set_feat_asset1_locale)
        index_feat_asset1_locale = self.feat_asset1_locale.findText("en-US: English (United States)", QtCore.Qt.MatchFixedString)
        self.feat_asset1_locale.setCurrentIndex(index_feat_asset1_locale)

        self.feat_asset2_role.clear()
        self.feat_asset2_role.addItems(settings.data_roles)
        self.feat_asset2_role.currentIndexChanged.connect(self.set_feat_asset2_role)

        self.feat_asset2_locale.clear()
        self.feat_asset2_locale.addItems(self.list_of_languages)
        self.feat_asset2_locale.currentIndexChanged.connect(self.set_feat_asset2_locale)
        index_feat_asset2_locale = self.feat_asset2_locale.findText("en-US: English (United States)", QtCore.Qt.MatchFixedString)
        self.feat_asset2_locale.setCurrentIndex(index_feat_asset2_locale)

        self.feat_asset3_role.clear()
        self.feat_asset3_role.addItems(settings.data_roles)
        self.feat_asset3_role.currentIndexChanged.connect(self.set_feat_asset3_role)

        self.feat_asset3_locale.clear()
        self.feat_asset3_locale.addItems(self.list_of_languages)
        self.feat_asset3_locale.currentIndexChanged.connect(self.set_feat_asset3_locale)
        index_feat_asset3_locale = self.feat_asset3_locale.findText("en-US: English (United States)", QtCore.Qt.MatchFixedString)
        self.feat_asset3_locale.setCurrentIndex(index_feat_asset3_locale)

        self.feat_asset4_role.clear()
        self.feat_asset4_role.addItems(settings.data_roles)
        self.feat_asset4_role.currentIndexChanged.connect(self.set_feat_asset4_role)

        self.feat_asset4_locale.clear()
        self.feat_asset4_locale.addItems(self.list_of_languages)
        self.feat_asset4_locale.currentIndexChanged.connect(self.set_feat_asset4_locale)
        index_feat_asset4_locale = self.feat_asset4_locale.findText("en-US: English (United States)", QtCore.Qt.MatchFixedString)
        self.feat_asset4_locale.setCurrentIndex(index_feat_asset4_locale)

        self.feat_asset5_role.clear()
        self.feat_asset5_role.addItems(settings.data_roles)
        self.feat_asset5_role.currentIndexChanged.connect(self.set_feat_asset5_role)

        self.feat_asset5_locale.clear()
        self.feat_asset5_locale.addItems(self.list_of_languages)
        self.feat_asset5_locale.currentIndexChanged.connect(self.set_feat_asset5_locale)
        index_feat_asset5_locale = self.feat_asset5_locale.findText("en-US: English (United States)", QtCore.Qt.MatchFixedString)
        self.feat_asset5_locale.setCurrentIndex(index_feat_asset5_locale)

        self.feat_asset6_role.clear()
        self.feat_asset6_role.addItems(settings.data_roles)
        self.feat_asset6_role.currentIndexChanged.connect(self.set_feat_asset6_role)

        self.feat_asset6_locale.clear()
        self.feat_asset6_locale.addItems(self.list_of_languages)
        self.feat_asset6_locale.currentIndexChanged.connect(self.set_feat_asset6_locale)
        index_feat_asset6_locale = self.feat_asset6_locale.findText("en-US: English (United States)", QtCore.Qt.MatchFixedString)
        self.feat_asset6_locale.setCurrentIndex(index_feat_asset6_locale)

        self.feat_asset7_role.clear()
        self.feat_asset7_role.addItems(settings.data_roles)
        self.feat_asset7_role.currentIndexChanged.connect(self.set_feat_asset7_role)

        self.feat_asset7_locale.clear()
        self.feat_asset7_locale.addItems(self.list_of_languages)
        self.feat_asset7_locale.currentIndexChanged.connect(self.set_feat_asset7_locale)
        index_feat_asset7_locale = self.feat_asset7_locale.findText("en-US: English (United States)", QtCore.Qt.MatchFixedString)
        self.feat_asset7_locale.setCurrentIndex(index_feat_asset7_locale)

        self.feat_asset8_role.clear()
        self.feat_asset8_role.addItems(settings.data_roles)
        self.feat_asset8_role.currentIndexChanged.connect(self.set_feat_asset8_role)

        self.feat_asset8_locale.clear()
        self.feat_asset8_locale.addItems(self.list_of_languages)
        self.feat_asset8_locale.currentIndexChanged.connect(self.set_feat_asset8_locale)
        index_feat_asset8_locale = self.feat_asset8_locale.findText("en-US: English (United States)", QtCore.Qt.MatchFixedString)
        self.feat_asset8_locale.setCurrentIndex(index_feat_asset8_locale)

        self.feat_asset1_add_terr.clicked.connect(self.feat_asset1_add)
        self.feat_asset1_del_terr.clicked.connect(self.feat_asset1_del)
        self.feat_asset2_add_terr.clicked.connect(self.feat_asset2_add)
        self.feat_asset2_del_terr.clicked.connect(self.feat_asset2_del)
        self.feat_asset3_add_terr.clicked.connect(self.feat_asset3_add)
        self.feat_asset3_del_terr.clicked.connect(self.feat_asset3_del)
        self.feat_asset4_add_terr.clicked.connect(self.feat_asset4_add)
        self.feat_asset4_del_terr.clicked.connect(self.feat_asset4_del)
        self.feat_asset5_add_terr.clicked.connect(self.feat_asset5_add)
        self.feat_asset5_del_terr.clicked.connect(self.feat_asset5_del)
        self.feat_asset6_add_terr.clicked.connect(self.feat_asset6_add)
        self.feat_asset6_del_terr.clicked.connect(self.feat_asset6_del)
        self.feat_asset7_add_terr.clicked.connect(self.feat_asset7_add)
        self.feat_asset7_del_terr.clicked.connect(self.feat_asset7_del)
        self.feat_asset8_add_terr.clicked.connect(self.feat_asset8_add)
        self.feat_asset8_del_terr.clicked.connect(self.feat_asset8_del)

        # trailer assets
        self.trailer_asset1_btn.clicked.connect(self.trailer_asset1_dlg)
        self.trailer_asset2_btn.clicked.connect(self.trailer_asset2_dlg)
        self.trailer_asset3_btn.clicked.connect(self.trailer_asset3_dlg)
        self.trailer_asset4_btn.clicked.connect(self.trailer_asset4_dlg)
        self.trailer_asset5_btn.clicked.connect(self.trailer_asset5_dlg)
        self.trailer_asset6_btn.clicked.connect(self.trailer_asset6_dlg)
        self.trailer_asset7_btn.clicked.connect(self.trailer_asset7_dlg)
        self.trailer_asset8_btn.clicked.connect(self.trailer_asset8_dlg)

        self.trailer_asset1_role.clear()
        self.trailer_asset1_role.addItems(settings.data_roles)
        self.trailer_asset1_role.currentIndexChanged.connect(self.set_trailer_asset1_role)

        self.trailer_asset1_locale.clear()
        self.trailer_asset1_locale.addItems(self.list_of_languages)
        self.trailer_asset1_locale.currentIndexChanged.connect(self.set_trailer_asset1_locale)
        index_trailer_asset1_locale = self.trailer_asset1_locale.findText("en-US: English (United States)", QtCore.Qt.MatchFixedString)
        self.trailer_asset1_locale.setCurrentIndex(index_trailer_asset1_locale)

        self.trailer_asset2_role.clear()
        self.trailer_asset2_role.addItems(settings.data_roles)
        self.trailer_asset2_role.currentIndexChanged.connect(self.set_trailer_asset2_role)

        self.trailer_asset2_locale.clear()
        self.trailer_asset2_locale.addItems(self.list_of_languages)
        self.trailer_asset2_locale.currentIndexChanged.connect(self.set_trailer_asset2_locale)
        index_trailer_asset2_locale = self.trailer_asset2_locale.findText("en-US: English (United States)", QtCore.Qt.MatchFixedString)
        self.trailer_asset2_locale.setCurrentIndex(index_trailer_asset2_locale)

        self.trailer_asset3_role.clear()
        self.trailer_asset3_role.addItems(settings.data_roles)
        self.trailer_asset3_role.currentIndexChanged.connect(self.set_trailer_asset3_role)

        self.trailer_asset3_locale.clear()
        self.trailer_asset3_locale.addItems(self.list_of_languages)
        self.trailer_asset3_locale.currentIndexChanged.connect(self.set_trailer_asset3_locale)
        index_trailer_asset3_locale = self.trailer_asset3_locale.findText("en-US: English (United States)", QtCore.Qt.MatchFixedString)
        self.trailer_asset3_locale.setCurrentIndex(index_trailer_asset3_locale)

        self.trailer_asset4_role.clear()
        self.trailer_asset4_role.addItems(settings.data_roles)
        self.trailer_asset4_role.currentIndexChanged.connect(self.set_trailer_asset4_role)

        self.trailer_asset4_locale.clear()
        self.trailer_asset4_locale.addItems(self.list_of_languages)
        self.trailer_asset4_locale.currentIndexChanged.connect(self.set_trailer_asset4_locale)
        index_trailer_asset4_locale = self.trailer_asset4_locale.findText("en-US: English (United States)", QtCore.Qt.MatchFixedString)
        self.trailer_asset4_locale.setCurrentIndex(index_trailer_asset4_locale)

        self.trailer_asset5_role.clear()
        self.trailer_asset5_role.addItems(settings.data_roles)
        self.trailer_asset5_role.currentIndexChanged.connect(self.set_trailer_asset5_role)

        self.trailer_asset5_locale.clear()
        self.trailer_asset5_locale.addItems(self.list_of_languages)
        self.trailer_asset5_locale.currentIndexChanged.connect(self.set_trailer_asset5_locale)
        index_trailer_asset5_locale = self.trailer_asset5_locale.findText("en-US: English (United States)", QtCore.Qt.MatchFixedString)
        self.trailer_asset5_locale.setCurrentIndex(index_trailer_asset5_locale)

        self.trailer_asset6_role.clear()
        self.trailer_asset6_role.addItems(settings.data_roles)
        self.trailer_asset6_role.currentIndexChanged.connect(self.set_trailer_asset6_role)

        self.trailer_asset6_locale.clear()
        self.trailer_asset6_locale.addItems(self.list_of_languages)
        self.trailer_asset6_locale.currentIndexChanged.connect(self.set_trailer_asset6_locale)
        index_trailer_asset6_locale = self.trailer_asset6_locale.findText("en-US: English (United States)", QtCore.Qt.MatchFixedString)
        self.trailer_asset6_locale.setCurrentIndex(index_trailer_asset6_locale)

        self.trailer_asset7_role.clear()
        self.trailer_asset7_role.addItems(settings.data_roles)
        self.trailer_asset7_role.currentIndexChanged.connect(self.set_trailer_asset7_role)

        self.trailer_asset7_locale.clear()
        self.trailer_asset7_locale.addItems(self.list_of_languages)
        self.trailer_asset7_locale.currentIndexChanged.connect(self.set_trailer_asset7_locale)
        index_trailer_asset7_locale = self.trailer_asset7_locale.findText("en-US: English (United States)", QtCore.Qt.MatchFixedString)
        self.trailer_asset7_locale.setCurrentIndex(index_trailer_asset7_locale)

        self.trailer_asset8_role.clear()
        self.trailer_asset8_role.addItems(settings.data_roles)
        self.trailer_asset8_role.currentIndexChanged.connect(self.set_trailer_asset8_role)

        self.trailer_asset8_locale.clear()
        self.trailer_asset8_locale.addItems(self.list_of_languages)
        self.trailer_asset8_locale.currentIndexChanged.connect(self.set_trailer_asset8_locale)
        index_trailer_asset8_locale = self.trailer_asset8_locale.findText("en-US: English (United States)", QtCore.Qt.MatchFixedString)
        self.trailer_asset8_locale.setCurrentIndex(index_trailer_asset8_locale)

        # poster
        self.comboPoster.clear()
        self.comboPoster.addItems(self.list_of_languages)
        self.comboPoster.currentIndexChanged.connect(self.set_poster_locale)
        index_poster_locale = self.comboPoster.findText("en-US: English (United States)", QtCore.Qt.MatchFixedString)
        self.comboPoster.setCurrentIndex(index_poster_locale)

        self.poster_file_btn.clicked.connect(self.poster_file_dlg)

        # product
        self.product1_check.stateChanged.connect(self.set_product1_check)
        self.product2_check.stateChanged.connect(self.set_product2_check)
        self.product3_check.stateChanged.connect(self.set_product3_check)
        self.product4_check.stateChanged.connect(self.set_product4_check)
        
        self.product1_sales_start_check.stateChanged.connect(self.set_product1_sales_start_check)
        self.product2_sales_start_check.stateChanged.connect(self.set_product2_sales_start_check)
        self.product3_sales_start_check.stateChanged.connect(self.set_product3_sales_start_check)
        self.product4_sales_start_check.stateChanged.connect(self.set_product4_sales_start_check)
        
        self.product1_sales_end_check.stateChanged.connect(self.set_product1_sales_end_check)
        self.product2_sales_end_check.stateChanged.connect(self.set_product2_sales_end_check)
        self.product3_sales_end_check.stateChanged.connect(self.set_product3_sales_end_check)
        self.product4_sales_end_check.stateChanged.connect(self.set_product4_sales_end_check)
        
        self.product1_preorder_check.stateChanged.connect(self.set_product1_preorder_check)
        self.product2_preorder_check.stateChanged.connect(self.set_product2_preorder_check)
        self.product3_preorder_check.stateChanged.connect(self.set_product3_preorder_check)
        self.product4_preorder_check.stateChanged.connect(self.set_product4_preorder_check)
        
        self.product1_vod_start_check.stateChanged.connect(self.set_product1_vod_start_check)
        self.product2_vod_start_check.stateChanged.connect(self.set_product2_vod_start_check)
        self.product3_vod_start_check.stateChanged.connect(self.set_product3_vod_start_check)
        self.product4_vod_start_check.stateChanged.connect(self.set_product4_vod_start_check)
        
        self.product1_vod_end_check.stateChanged.connect(self.set_product1_vod_end_check)
        self.product2_vod_end_check.stateChanged.connect(self.set_product2_vod_end_check)
        self.product3_vod_end_check.stateChanged.connect(self.set_product3_vod_end_check)
        self.product4_vod_end_check.stateChanged.connect(self.set_product4_vod_end_check)
        
        self.product1_physical_check.stateChanged.connect(self.set_product1_physical_check)
        self.product2_physical_check.stateChanged.connect(self.set_product2_physical_check)
        self.product3_physical_check.stateChanged.connect(self.set_product3_physical_check)
        self.product4_physical_check.stateChanged.connect(self.set_product4_physical_check)

        self.product1_price_sd_check.stateChanged.connect(self.set_product1_price_sd_check)
        self.product2_price_sd_check.stateChanged.connect(self.set_product2_price_sd_check)
        self.product3_price_sd_check.stateChanged.connect(self.set_product3_price_sd_check)
        self.product4_price_sd_check.stateChanged.connect(self.set_product4_price_sd_check)

        self.product1_price_hd_check.stateChanged.connect(self.set_product1_price_hd_check)
        self.product2_price_hd_check.stateChanged.connect(self.set_product2_price_hd_check)
        self.product3_price_hd_check.stateChanged.connect(self.set_product3_price_hd_check)
        self.product4_price_hd_check.stateChanged.connect(self.set_product4_price_hd_check)

        self.product1_vod_type_check.stateChanged.connect(self.set_product1_vod_type_check)
        self.product2_vod_type_check.stateChanged.connect(self.set_product2_vod_type_check)
        self.product3_vod_type_check.stateChanged.connect(self.set_product3_vod_type_check)
        self.product4_vod_type_check.stateChanged.connect(self.set_product4_vod_type_check)

        self.product1_terr.clear()
        self.product1_terr.addItems(self.country_values)
        self.product1_terr.currentIndexChanged.connect(self.set_product1_terr)
        index_product1_terr = self.product1_terr.findText("US", QtCore.Qt.MatchFixedString)
        self.product1_terr.setCurrentIndex(index_product1_terr)

        self.product1_sale_clear.clear()
        self.product1_sale_clear.addItems(settings.cleared_choices)
        self.product1_sale_clear.currentIndexChanged.connect(self.set_product1_sale_clear)

        self.product1_price_sd.textChanged.connect(self.set_product1_price_sd)
        self.product1_price_hd.textChanged.connect(self.set_product1_price_hd)
        
        self.product1_sales_start.textChanged.connect(self.set_product1_sales_start)
        self.product1_sales_end.textChanged.connect(self.set_product1_sales_end)
        self.product1_preorder.textChanged.connect(self.set_product1_preorder)

        self.product1_vod_clear.clear()
        self.product1_vod_clear.addItems(settings.cleared_choices)
        self.product1_vod_clear.currentIndexChanged.connect(self.set_product1_vod_clear)

        self.product1_vod_type.clear()
        self.product1_vod_type.addItems(settings.vod_types)
        self.product1_vod_type.currentIndexChanged.connect(self.set_product1_vod_type)

        self.product1_vod_start.textChanged.connect(self.set_product1_vod_start)
        self.product1_vod_end.textChanged.connect(self.set_product1_vod_end)
        self.product1_physical.textChanged.connect(self.set_product1_physical)

        self.product2_terr.clear()
        self.product2_terr.addItems(self.country_values)
        self.product2_terr.currentIndexChanged.connect(self.set_product2_terr)
        index_product2_terr = self.product2_terr.findText("US", QtCore.Qt.MatchFixedString)
        self.product2_terr.setCurrentIndex(index_product2_terr)

        self.product2_sale_clear.clear()
        self.product2_sale_clear.addItems(settings.cleared_choices)
        self.product2_sale_clear.currentIndexChanged.connect(self.set_product2_sale_clear)

        self.product2_price_sd.textChanged.connect(self.set_product2_price_sd)
        self.product2_price_hd.textChanged.connect(self.set_product2_price_hd)
        
        self.product2_sales_start.textChanged.connect(self.set_product2_sales_start)
        self.product2_sales_end.textChanged.connect(self.set_product2_sales_end)
        self.product2_preorder.textChanged.connect(self.set_product2_preorder)

        self.product2_vod_clear.clear()
        self.product2_vod_clear.addItems(settings.cleared_choices)
        self.product2_vod_clear.currentIndexChanged.connect(self.set_product2_vod_clear)

        self.product2_vod_type.clear()
        self.product2_vod_type.addItems(settings.vod_types)
        self.product2_vod_type.currentIndexChanged.connect(self.set_product2_vod_type)

        self.product2_vod_start.textChanged.connect(self.set_product2_vod_start)
        self.product2_vod_end.textChanged.connect(self.set_product2_vod_end)
        self.product2_physical.textChanged.connect(self.set_product2_physical)

        self.product3_terr.clear()
        self.product3_terr.addItems(self.country_values)
        self.product3_terr.currentIndexChanged.connect(self.set_product3_terr)
        index_product3_terr = self.product3_terr.findText("US", QtCore.Qt.MatchFixedString)
        self.product3_terr.setCurrentIndex(index_product3_terr)

        self.product3_sale_clear.clear()
        self.product3_sale_clear.addItems(settings.cleared_choices)
        self.product3_sale_clear.currentIndexChanged.connect(self.set_product3_sale_clear)

        self.product3_price_sd.textChanged.connect(self.set_product3_price_sd)
        self.product3_price_hd.textChanged.connect(self.set_product3_price_hd)
        
        self.product3_sales_start.textChanged.connect(self.set_product3_sales_start)
        self.product3_sales_end.textChanged.connect(self.set_product3_sales_end)
        self.product3_preorder.textChanged.connect(self.set_product3_preorder)

        self.product3_vod_clear.clear()
        self.product3_vod_clear.addItems(settings.cleared_choices)
        self.product3_vod_clear.currentIndexChanged.connect(self.set_product3_vod_clear)

        self.product3_vod_type.clear()
        self.product3_vod_type.addItems(settings.vod_types)
        self.product3_vod_type.currentIndexChanged.connect(self.set_product3_vod_type)

        self.product3_vod_start.textChanged.connect(self.set_product3_vod_start)
        self.product3_vod_end.textChanged.connect(self.set_product3_vod_end)
        self.product3_physical.textChanged.connect(self.set_product3_physical)

        self.product4_terr.clear()
        self.product4_terr.addItems(self.country_values)
        self.product4_terr.currentIndexChanged.connect(self.set_product4_terr)
        index_product4_terr = self.product4_terr.findText("US", QtCore.Qt.MatchFixedString)
        self.product4_terr.setCurrentIndex(index_product4_terr)

        self.product4_sale_clear.clear()
        self.product4_sale_clear.addItems(settings.cleared_choices)
        self.product4_sale_clear.currentIndexChanged.connect(self.set_product4_sale_clear)

        self.product4_price_sd.textChanged.connect(self.set_product4_price_sd)
        self.product4_price_hd.textChanged.connect(self.set_product4_price_hd)
        
        self.product4_sales_start.textChanged.connect(self.set_product4_sales_start)
        self.product4_sales_end.textChanged.connect(self.set_product4_sales_end)
        self.product4_preorder.textChanged.connect(self.set_product4_preorder)

        self.product4_vod_clear.clear()
        self.product4_vod_clear.addItems(settings.cleared_choices)
        self.product4_vod_clear.currentIndexChanged.connect(self.set_product4_vod_clear)

        self.product4_vod_type.clear()
        self.product4_vod_type.addItems(settings.vod_types)
        self.product4_vod_type.currentIndexChanged.connect(self.set_product4_vod_type)

        self.product4_vod_start.textChanged.connect(self.set_product4_vod_start)
        self.product4_vod_end.textChanged.connect(self.set_product4_vod_end)
        self.product4_physical.textChanged.connect(self.set_product4_physical)

        # localization
        self.localized_check_1.stateChanged.connect(self.set_localized_check_1)
        self.localized_locale_1.clear()
        self.localized_locale_1.addItems(self.list_of_languages)
        self.localized_locale_1.currentIndexChanged.connect(self.set_localized_locale_1)
        index_localized_locale_1 = self.localized_locale_1.findText("en-US: English (United States)",
                                                                    QtCore.Qt.MatchFixedString)
        self.localized_locale_1.setCurrentIndex(index_localized_locale_1)
        self.localized_title_1.textChanged.connect(self.set_localized_title_1)
        self.localized_synopsis_1.textChanged.connect(self.set_localized_synopsis_1)

        self.localized_check_2.stateChanged.connect(self.set_localized_check_2)
        self.localized_locale_2.clear()
        self.localized_locale_2.addItems(self.list_of_languages)
        self.localized_locale_2.currentIndexChanged.connect(self.set_localized_locale_2)
        index_localized_locale_2 = self.localized_locale_2.findText("en-US: English (United States)",
                                                                  QtCore.Qt.MatchFixedString)
        self.localized_locale_2.setCurrentIndex(index_localized_locale_2)
        self.localized_title_2.textChanged.connect(self.set_localized_title_2)
        self.localized_synopsis_2.textChanged.connect(self.set_localized_synopsis_2)

        self.localized_check_3.stateChanged.connect(self.set_localized_check_3)
        self.localized_locale_3.clear()
        self.localized_locale_3.addItems(self.list_of_languages)
        self.localized_locale_3.currentIndexChanged.connect(self.set_localized_locale_3)
        index_localized_locale_3 = self.localized_locale_3.findText("en-US: English (United States)",
                                                                  QtCore.Qt.MatchFixedString)
        self.localized_locale_3.setCurrentIndex(index_localized_locale_3)
        self.localized_title_3.textChanged.connect(self.set_localized_title_3)
        self.localized_synopsis_3.textChanged.connect(self.set_localized_synopsis_3)

        self.localized_check_4.stateChanged.connect(self.set_localized_check_4)
        self.localized_locale_4.clear()
        self.localized_locale_4.addItems(self.list_of_languages)
        self.localized_locale_4.currentIndexChanged.connect(self.set_localized_locale_4)
        index_localized_locale_4 = self.localized_locale_4.findText("en-US: English (United States)",
                                                                  QtCore.Qt.MatchFixedString)
        self.localized_locale_4.setCurrentIndex(index_localized_locale_4)
        self.localized_title_4.textChanged.connect(self.set_localized_title_4)
        self.localized_synopsis_4.textChanged.connect(self.set_localized_synopsis_4)

        # localized trailer
        tc_lst = settings.timecodes.keys()
        tc_lst.sort()
        self.tc_format_loc_trailer.clear()
        self.tc_format_loc_trailer.addItems(tc_lst)
        self.tc_format_loc_trailer.currentIndexChanged.connect(self.set_loc_trailer_tc_format)
        index_tc_format_loc = self.tc_format_loc_trailer.findText("23.98fps", QtCore.Qt.MatchFixedString)
        self.tc_format_loc_trailer.setCurrentIndex(index_tc_format_loc)

        self.loc_comboTrailerAudio.clear()
        self.loc_comboTrailerAudio.addItems(self.list_of_languages)
        self.loc_comboTrailerAudio.currentIndexChanged.connect(self.set_loc_trailer_audio)
        index_loc_comboTrailerAudio = self.loc_comboTrailerAudio.findText("en-US: English (United States)", QtCore.Qt.MatchFixedString)
        self.loc_comboTrailerAudio.setCurrentIndex(index_loc_comboTrailerAudio)

        self.loc_comboNarrTrailer.clear()
        self.loc_comboNarrTrailer.addItems(self.list_of_languages)
        self.loc_comboNarrTrailer.currentIndexChanged.connect(self.set_narr_loc_trailer)
        index_loc_comboNarrTrailer = self.loc_comboNarrTrailer.findText("en-US: English (United States)", QtCore.Qt.MatchFixedString)
        self.loc_comboNarrTrailer.setCurrentIndex(index_loc_comboNarrTrailer)

        self.loc_comboSubTrailer.clear()
        self.loc_comboSubTrailer.addItems(self.list_of_languages)
        self.loc_comboSubTrailer.currentIndexChanged.connect(self.set_sub_loc_trailer)
        index_loc_comboSubTrailer = self.loc_comboSubTrailer.findText("en-US: English (United States)", QtCore.Qt.MatchFixedString)
        self.loc_comboSubTrailer.setCurrentIndex(index_loc_comboSubTrailer)

        self.loc_trailer_still_tc.textChanged.connect(self.set_loc_trailer_still_tc)

        self.loc_trailer_top_crop.textChanged.connect(self.set_loc_trailer_top_crop)
        self.loc_trailer_bottom_crop.textChanged.connect(self.set_loc_trailer_bottom_crop)
        self.loc_trailer_left_crop.textChanged.connect(self.set_loc_trailer_left_crop)
        self.loc_trailer_right_crop.textChanged.connect(self.set_loc_trailer_right_crop)

        self.loc_trailer_file.clicked.connect(self.loc_trailer_file_dlg)
        self.loc_trailer_md5_start_btn.clicked.connect(self.loc_trailer_md5_start)
        self.loc_trailer_md5_stop_btn.clicked.connect(self.loc_trailer_md5_stop)
        self.loc_trailer_md5_lbl.textChanged.connect(self.set_loc_trailer_md5_lbl)

        self.loc_trailer_narr.stateChanged.connect(self.check_loc_trailer_narr)
        self.loc_trailer_subs.stateChanged.connect(self.check_loc_trailer_subs)

        self.add_territory_btn.clicked.connect(self.add_territory)
        self.del_territory_btn.clicked.connect(self.del_territory)

        self.add_territory()

        # localized trailer assets
        self.loc_trailer_asset1_btn.clicked.connect(self.loc_trailer_asset1_dlg)
        self.loc_trailer_asset2_btn.clicked.connect(self.loc_trailer_asset2_dlg)
        self.loc_trailer_asset3_btn.clicked.connect(self.loc_trailer_asset3_dlg)
        self.loc_trailer_asset4_btn.clicked.connect(self.loc_trailer_asset4_dlg)
        self.loc_trailer_asset5_btn.clicked.connect(self.loc_trailer_asset5_dlg)
        self.loc_trailer_asset6_btn.clicked.connect(self.loc_trailer_asset6_dlg)
        self.loc_trailer_asset7_btn.clicked.connect(self.loc_trailer_asset7_dlg)
        self.loc_trailer_asset8_btn.clicked.connect(self.loc_trailer_asset8_dlg)

        self.loc_trailer_asset1_role.clear()
        self.loc_trailer_asset1_role.addItems(settings.data_roles)
        self.loc_trailer_asset1_role.currentIndexChanged.connect(self.set_loc_trailer_asset1_role)

        self.loc_trailer_asset1_locale.clear()
        self.loc_trailer_asset1_locale.addItems(self.list_of_languages)
        self.loc_trailer_asset1_locale.currentIndexChanged.connect(self.set_loc_trailer_asset1_locale)
        index_loc_trailer_asset1_locale = self.loc_trailer_asset1_locale.findText("en-US: English (United States)",
                                                                          QtCore.Qt.MatchFixedString)
        self.loc_trailer_asset1_locale.setCurrentIndex(index_loc_trailer_asset1_locale)

        self.loc_trailer_asset2_role.clear()
        self.loc_trailer_asset2_role.addItems(settings.data_roles)
        self.loc_trailer_asset2_role.currentIndexChanged.connect(self.set_loc_trailer_asset2_role)

        self.loc_trailer_asset2_locale.clear()
        self.loc_trailer_asset2_locale.addItems(self.list_of_languages)
        self.loc_trailer_asset2_locale.currentIndexChanged.connect(self.set_loc_trailer_asset2_locale)
        index_loc_trailer_asset2_locale = self.loc_trailer_asset2_locale.findText("en-US: English (United States)",
                                                                          QtCore.Qt.MatchFixedString)
        self.loc_trailer_asset2_locale.setCurrentIndex(index_loc_trailer_asset2_locale)

        self.loc_trailer_asset3_role.clear()
        self.loc_trailer_asset3_role.addItems(settings.data_roles)
        self.loc_trailer_asset3_role.currentIndexChanged.connect(self.set_loc_trailer_asset3_role)

        self.loc_trailer_asset3_locale.clear()
        self.loc_trailer_asset3_locale.addItems(self.list_of_languages)
        self.loc_trailer_asset3_locale.currentIndexChanged.connect(self.set_loc_trailer_asset3_locale)
        index_loc_trailer_asset3_locale = self.loc_trailer_asset3_locale.findText("en-US: English (United States)",
                                                                          QtCore.Qt.MatchFixedString)
        self.loc_trailer_asset3_locale.setCurrentIndex(index_loc_trailer_asset3_locale)

        self.loc_trailer_asset4_role.clear()
        self.loc_trailer_asset4_role.addItems(settings.data_roles)
        self.loc_trailer_asset4_role.currentIndexChanged.connect(self.set_loc_trailer_asset4_role)

        self.loc_trailer_asset4_locale.clear()
        self.loc_trailer_asset4_locale.addItems(self.list_of_languages)
        self.loc_trailer_asset4_locale.currentIndexChanged.connect(self.set_loc_trailer_asset4_locale)
        index_loc_trailer_asset4_locale = self.loc_trailer_asset4_locale.findText("en-US: English (United States)",
                                                                          QtCore.Qt.MatchFixedString)
        self.loc_trailer_asset4_locale.setCurrentIndex(index_loc_trailer_asset4_locale)

        self.loc_trailer_asset5_role.clear()
        self.loc_trailer_asset5_role.addItems(settings.data_roles)
        self.loc_trailer_asset5_role.currentIndexChanged.connect(self.set_loc_trailer_asset5_role)

        self.loc_trailer_asset5_locale.clear()
        self.loc_trailer_asset5_locale.addItems(self.list_of_languages)
        self.loc_trailer_asset5_locale.currentIndexChanged.connect(self.set_loc_trailer_asset5_locale)
        index_loc_trailer_asset5_locale = self.loc_trailer_asset5_locale.findText("en-US: English (United States)",
                                                                          QtCore.Qt.MatchFixedString)
        self.loc_trailer_asset5_locale.setCurrentIndex(index_loc_trailer_asset5_locale)

        self.loc_trailer_asset6_role.clear()
        self.loc_trailer_asset6_role.addItems(settings.data_roles)
        self.loc_trailer_asset6_role.currentIndexChanged.connect(self.set_loc_trailer_asset6_role)

        self.loc_trailer_asset6_locale.clear()
        self.loc_trailer_asset6_locale.addItems(self.list_of_languages)
        self.loc_trailer_asset6_locale.currentIndexChanged.connect(self.set_loc_trailer_asset6_locale)
        index_loc_trailer_asset6_locale = self.loc_trailer_asset6_locale.findText("en-US: English (United States)",
                                                                          QtCore.Qt.MatchFixedString)
        self.loc_trailer_asset6_locale.setCurrentIndex(index_loc_trailer_asset6_locale)

        self.loc_trailer_asset7_role.clear()
        self.loc_trailer_asset7_role.addItems(settings.data_roles)
        self.loc_trailer_asset7_role.currentIndexChanged.connect(self.set_loc_trailer_asset7_role)

        self.loc_trailer_asset7_locale.clear()
        self.loc_trailer_asset7_locale.addItems(self.list_of_languages)
        self.loc_trailer_asset7_locale.currentIndexChanged.connect(self.set_loc_trailer_asset7_locale)
        index_loc_trailer_asset7_locale = self.loc_trailer_asset7_locale.findText("en-US: English (United States)",
                                                                          QtCore.Qt.MatchFixedString)
        self.loc_trailer_asset7_locale.setCurrentIndex(index_loc_trailer_asset7_locale)

        self.loc_trailer_asset8_role.clear()
        self.loc_trailer_asset8_role.addItems(settings.data_roles)
        self.loc_trailer_asset8_role.currentIndexChanged.connect(self.set_loc_trailer_asset8_role)

        self.loc_trailer_asset8_locale.clear()
        self.loc_trailer_asset8_locale.addItems(self.list_of_languages)
        self.loc_trailer_asset8_locale.currentIndexChanged.connect(self.set_loc_trailer_asset8_locale)
        index_loc_trailer_asset8_locale = self.loc_trailer_asset8_locale.findText("en-US: English (United States)",
                                                                          QtCore.Qt.MatchFixedString)
        self.loc_trailer_asset8_locale.setCurrentIndex(index_loc_trailer_asset8_locale)

        # process
        self.comboProvider.clear()
        self.comboProvider.addItems(settings.providers_lst)
        self.comboProvider.currentIndexChanged.connect(self.set_provider)
        index_provider = self.comboProvider.findText("Entertainment One US LP: KochDistribution", QtCore.Qt.MatchFixedString)
        self.comboProvider.setCurrentIndex(index_provider)

        self.comboMetaLanguage.clear()
        self.comboMetaLanguage.addItems(self.list_of_languages)
        self.comboMetaLanguage.currentIndexChanged.connect(self.set_meta_locale)
        index_meta_language = self.comboMetaLanguage.findText("en-US: English (United States)", QtCore.Qt.MatchFixedString)
        self.comboMetaLanguage.setCurrentIndex(index_meta_language)

        self.vendor_id.textChanged.connect(self.set_vendor)
        # self.pack_info_path_btn.clicked.connect(self.pack_info_path_dlg)

        self.xml_dest_btn.clicked.connect(self.set_xml_dest)

        self.build_scenario.clear()
        self.build_scenario.addItems(settings.scenarios)
        self.build_scenario.currentIndexChanged.connect(self.set_build_scenario)

        self.process_btn.clicked.connect(self.process)
        self.process_stop_btn.clicked.connect(self.stop_process)

        self.reset_btn.clicked.connect(self.reset_app)

        self.show()

    # menubar
    @staticmethod
    def about_dlg():
        about = AboutDlg()
        about.exec_()

    def quit_fcn(self):
        self.close()

    # metadata
    def set_country(self):
        settings.country = str(self.comboCountry.currentText()).split(":", 1)[-1].lstrip()

    def set_spoken(self):
        settings.spoken = str(self.comboOriginalLanguage.currentText()).split(":", 1)[0]

    def set_title(self):
        title_clean = " ".join(unicode(self.adapted_title.text()).split())
        settings.title = title_clean

    def set_title_studio(self):
        studio_title_clean = " ".join(unicode(self.release_title.text()).split())
        settings.studio_title = studio_title_clean

    def set_synopsis(self):
        synopsis_clean = " ".join(unicode(self.synopsis.toPlainText()).split())
        settings.synopsis = synopsis_clean

    def set_company(self):
        self.production.setText(unicode(self.production.text()).lower().title())
        settings.company = " ".join(unicode(self.production.text()).split())

    def set_cline(self):
        self.copyright.setText(unicode(self.copyright.text()).lower().title())
        settings.cline = " ".join(unicode(self.copyright.text()).split())

    def set_theatrical(self):
        settings.theatrical = " ".join(unicode(self.theatrical.text()).split())

    # genres and ratings
    def set_genre1(self):
        settings.genre1 = genres.genres[str(self.genre1.currentText())]

    def set_genre2(self):
        settings.genre2 = genres.genres[str(self.genre2.currentText())]

    def set_genre3(self):
        settings.genre3 = genres.genres[str(self.genre3.currentText())]

    def set_genre4(self):
        settings.genre4 = genres.genres[str(self.genre4.currentText())]

    def set_genre5(self):
        settings.genre5 = genres.genres[str(self.genre5.currentText())]

    def set_genre6(self):
        settings.genre6 = genres.genres[str(self.genre6.currentText())]

    def set_genre7(self):
        settings.genre7 = genres.genres[str(self.genre7.currentText())]

    def set_genre8(self):
        settings.genre8 = genres.genres[str(self.genre8.currentText())]

    def set_rating1_sys(self):
        settings.rating1_sys = str(self.rating1_sys.currentText())

    def set_rating2_sys(self):
        settings.rating2_sys = str(self.rating2_sys.currentText())

    def set_rating3_sys(self):
        settings.rating3_sys = str(self.rating3_sys.currentText())

    def set_rating4_sys(self):
        settings.rating4_sys = str(self.rating4_sys.currentText())

    def set_rating5_sys(self):
        settings.rating5_sys = str(self.rating5_sys.currentText())

    def set_rating1_value(self):
        settings.rating1_value = " ".join(unicode(self.rating1_value.text()).split())

    def set_rating2_value(self):
        settings.rating2_value = " ".join(unicode(self.rating2_value.text()).split())

    def set_rating3_value(self):
        settings.rating3_value = " ".join(unicode(self.rating3_value.text()).split())

    def set_rating4_value(self):
        settings.rating4_value = " ".join(unicode(self.rating4_value.text()).split())

    def set_rating5_value(self):
        settings.rating5_value = " ".join(unicode(self.rating5_value.text()).split())

    # cast
    def set_actor1_name(self):
        settings.actor1_name = " ".join(unicode(self.actor1_name.text()).split())

    def set_actor2_name(self):
        settings.actor2_name = " ".join(unicode(self.actor2_name.text()).split())

    def set_actor3_name(self):
        settings.actor3_name = " ".join(unicode(self.actor3_name.text()).split())

    def set_actor4_name(self):
        settings.actor4_name = " ".join(unicode(self.actor4_name.text()).split())

    def set_actor5_name(self):
        settings.actor5_name = " ".join(unicode(self.actor5_name.text()).split())

    def set_actor6_name(self):
        settings.actor6_name = " ".join(unicode(self.actor6_name.text()).split())

    def set_actor7_name(self):
        settings.actor7_name = " ".join(unicode(self.actor7_name.text()).split())

    def set_actor8_name(self):
        settings.actor8_name = " ".join(unicode(self.actor8_name.text()).split())

    def set_actor9_name(self):
        settings.actor9_name = " ".join(unicode(self.actor9_name.text()).split())

    def set_actor10_name(self):
        settings.actor10_name = " ".join(unicode(self.actor10_name.text()).split())

    def set_actor1_char(self):
        settings.actor1_char = " ".join(unicode(self.actor1_char.text()).split())
        self.actor1_ref.setText(settings.actor1_char)

    def set_actor2_char(self):
        settings.actor2_char = " ".join(unicode(self.actor2_char.text()).split())
        self.actor2_ref.setText(settings.actor2_char)

    def set_actor3_char(self):
        settings.actor3_char = " ".join(unicode(self.actor3_char.text()).split())
        self.actor3_ref.setText(settings.actor3_char)

    def set_actor4_char(self):
        settings.actor4_char = " ".join(unicode(self.actor4_char.text()).split())
        self.actor4_ref.setText(settings.actor4_char)

    def set_actor5_char(self):
        settings.actor5_char = " ".join(unicode(self.actor5_char.text()).split())
        self.actor5_ref.setText(settings.actor5_char)

    def set_actor6_char(self):
        settings.actor6_char = " ".join(unicode(self.actor6_char.text()).split())
        self.actor6_ref.setText(settings.actor6_char)

    def set_actor7_char(self):
        settings.actor7_char = " ".join(unicode(self.actor7_char.text()).split())
        self.actor7_ref.setText(settings.actor7_char)

    def set_actor8_char(self):
        settings.actor8_char = " ".join(unicode(self.actor8_char.text()).split())
        self.actor8_ref.setText(settings.actor8_char)

    def set_actor9_char(self):
        settings.actor9_char = " ".join(unicode(self.actor9_char.text()).split())
        self.actor9_ref.setText(settings.actor9_char)

    def set_actor10_char(self):
        settings.actor10_char = " ".join(unicode(self.actor10_char.text()).split())
        self.actor10_ref.setText(settings.actor10_char)

    def set_actor1_char2(self):
        settings.actor1_char2 = " ".join(unicode(self.actor1_char2.text()).split())
        self.actor1_ref2.setText(settings.actor1_char2)

    def set_actor2_char2(self):
        settings.actor2_char2 = " ".join(unicode(self.actor2_char2.text()).split())
        self.actor2_ref2.setText(settings.actor2_char2)

    def set_actor3_char2(self):
        settings.actor3_char2 = " ".join(unicode(self.actor3_char2.text()).split())
        self.actor3_ref2.setText(settings.actor3_char2)

    def set_actor4_char2(self):
        settings.actor4_char2 = " ".join(unicode(self.actor4_char2.text()).split())
        self.actor4_ref2.setText(settings.actor4_char2)

    def set_actor5_char2(self):
        settings.actor5_char2 = " ".join(unicode(self.actor5_char2.text()).split())
        self.actor5_ref2.setText(settings.actor5_char2)

    def set_actor6_char2(self):
        settings.actor6_char2 = " ".join(unicode(self.actor6_char2.text()).split())
        self.actor6_ref2.setText(settings.actor6_char2)

    def set_actor7_char2(self):
        settings.actor7_char2 = " ".join(unicode(self.actor7_char2.text()).split())
        self.actor7_ref2.setText(settings.actor7_char2)

    def set_actor8_char2(self):
        settings.actor8_char2 = " ".join(unicode(self.actor8_char2.text()).split())
        self.actor8_ref2.setText(settings.actor8_char2)

    def set_actor9_char2(self):
        settings.actor9_char2 = " ".join(unicode(self.actor9_char2.text()).split())
        self.actor9_ref2.setText(settings.actor9_char2)

    def set_actor10_char2(self):
        settings.actor10_char2 = " ".join(unicode(self.actor10_char2.text()).split())
        self.actor10_ref2.setText(settings.actor10_char2)

    def set_actor1_apple_id(self):
        settings.actor1_apple_id = " ".join(unicode(self.actor1_apple_id.text()).split())

    def set_actor2_apple_id(self):
        settings.actor2_apple_id = " ".join(unicode(self.actor2_apple_id.text()).split())

    def set_actor3_apple_id(self):
        settings.actor3_apple_id = " ".join(unicode(self.actor3_apple_id.text()).split())

    def set_actor4_apple_id(self):
        settings.actor4_apple_id = " ".join(unicode(self.actor4_apple_id.text()).split())

    def set_actor5_apple_id(self):
        settings.actor5_apple_id = " ".join(unicode(self.actor5_apple_id.text()).split())

    def set_actor6_apple_id(self):
        settings.actor6_apple_id = " ".join(unicode(self.actor6_apple_id.text()).split())

    def set_actor7_apple_id(self):
        settings.actor7_apple_id = " ".join(unicode(self.actor7_apple_id.text()).split())

    def set_actor8_apple_id(self):
        settings.actor8_apple_id = " ".join(unicode(self.actor8_apple_id.text()).split())

    def set_actor9_apple_id(self):
        settings.actor9_apple_id = " ".join(unicode(self.actor9_apple_id.text()).split())

    def set_actor10_apple_id(self):
        settings.actor10_apple_id = " ".join(unicode(self.actor10_apple_id.text()).split())

    def set_actor1_ref(self):
        self.actor1_ref.setText(unidecode(unicode(self.actor1_ref.text())).upper().replace(" ", "_").replace("-", "_"))
        settings.actor1_ref = " ".join(unicode(self.actor1_ref.text()).split())

    def set_actor2_ref(self):
        self.actor2_ref.setText(unidecode(unicode(self.actor2_ref.text())).upper().replace(" ", "_").replace("-", "_"))
        settings.actor2_ref = " ".join(unicode(self.actor2_ref.text()).split())

    def set_actor3_ref(self):
        self.actor3_ref.setText(unidecode(unicode(self.actor3_ref.text())).upper().replace(" ", "_").replace("-", "_"))
        settings.actor3_ref = " ".join(unicode(self.actor3_ref.text()).split())

    def set_actor4_ref(self):
        self.actor4_ref.setText(unidecode(unicode(self.actor4_ref.text())).upper().replace(" ", "_").replace("-", "_"))
        settings.actor4_ref = " ".join(unicode(self.actor4_ref.text()).split())

    def set_actor5_ref(self):
        self.actor5_ref.setText(unidecode(unicode(self.actor5_ref.text())).upper().replace(" ", "_").replace("-", "_"))
        settings.actor5_ref = " ".join(unicode(self.actor5_ref.text()).split())

    def set_actor6_ref(self):
        self.actor6_ref.setText(unidecode(unicode(self.actor6_ref.text())).upper().replace(" ", "_").replace("-", "_"))
        settings.actor6_ref = " ".join(unicode(self.actor6_ref.text()).split())

    def set_actor7_ref(self):
        self.actor7_ref.setText(unidecode(unicode(self.actor7_ref.text())).upper().replace(" ", "_").replace("-", "_"))
        settings.actor7_ref = " ".join(unicode(self.actor7_ref.text()).split())

    def set_actor8_ref(self):
        self.actor8_ref.setText(unidecode(unicode(self.actor8_ref.text())).upper().replace(" ", "_").replace("-", "_"))
        settings.actor8_ref = " ".join(unicode(self.actor8_ref.text()).split())

    def set_actor9_ref(self):
        self.actor9_ref.setText(unidecode(unicode(self.actor9_ref.text())).upper().replace(" ", "_").replace("-", "_"))
        settings.actor9_ref = " ".join(unicode(self.actor9_ref.text()).split())

    def set_actor10_ref(self):
        self.actor10_ref.setText(unidecode(unicode(self.actor10_ref.text())).upper().replace(" ", "_").replace("-", "_"))
        settings.actor10_ref = " ".join(unicode(self.actor10_ref.text()).split())

    def set_actor1_ref2(self):
        self.actor1_ref2.setText(unidecode(unicode(self.actor1_ref2.text())).upper().replace(" ", "_").replace("-", "_"))
        settings.actor1_ref2 = " ".join(unicode(self.actor1_ref2.text()).split())

    def set_actor2_ref2(self):
        self.actor2_ref2.setText(
            unidecode(unicode(self.actor2_ref2.text())).upper().replace(" ", "_").replace("-", "_"))
        settings.actor2_ref2 = " ".join(unicode(self.actor2_ref2.text()).split())

    def set_actor3_ref2(self):
        self.actor3_ref2.setText(
            unidecode(unicode(self.actor3_ref2.text())).upper().replace(" ", "_").replace("-", "_"))
        settings.actor3_ref2 = " ".join(unicode(self.actor3_ref2.text()).split())

    def set_actor4_ref2(self):
        self.actor4_ref2.setText(
            unidecode(unicode(self.actor4_ref2.text())).upper().replace(" ", "_").replace("-", "_"))
        settings.actor4_ref2 = " ".join(unicode(self.actor4_ref2.text()).split())

    def set_actor5_ref2(self):
        self.actor5_ref2.setText(
            unidecode(unicode(self.actor5_ref2.text())).upper().replace(" ", "_").replace("-", "_"))
        settings.actor5_ref2 = " ".join(unicode(self.actor5_ref2.text()).split())

    def set_actor6_ref2(self):
        self.actor6_ref2.setText(
            unidecode(unicode(self.actor6_ref2.text())).upper().replace(" ", "_").replace("-", "_"))
        settings.actor6_ref2 = " ".join(unicode(self.actor6_ref2.text()).split())

    def set_actor7_ref2(self):
        self.actor7_ref2.setText(
            unidecode(unicode(self.actor7_ref2.text())).upper().replace(" ", "_").replace("-", "_"))
        settings.actor7_ref2 = " ".join(unicode(self.actor7_ref2.text()).split())

    def set_actor8_ref2(self):
        self.actor8_ref2.setText(
            unidecode(unicode(self.actor8_ref2.text())).upper().replace(" ", "_").replace("-", "_"))
        settings.actor8_ref2 = " ".join(unicode(self.actor8_ref2.text()).split())

    def set_actor9_ref2(self):
        self.actor9_ref2.setText(
            unidecode(unicode(self.actor9_ref2.text())).upper().replace(" ", "_").replace("-", "_"))
        settings.actor9_ref2 = " ".join(unicode(self.actor9_ref2.text()).split())

    def set_actor10_ref2(self):
        self.actor10_ref2.setText(
            unidecode(unicode(self.actor10_ref2.text())).upper().replace(" ", "_").replace("-", "_"))
        settings.actor10_ref2 = " ".join(unicode(self.actor10_ref2.text()).split())

    # crew
    def set_crew1_name(self):
        settings.crew1_name = " ".join(unicode(self.crew1_name.text()).split())

    def set_crew2_name(self):
        settings.crew2_name = " ".join(unicode(self.crew2_name.text()).split())

    def set_crew3_name(self):
        settings.crew3_name = " ".join(unicode(self.crew3_name.text()).split())

    def set_crew4_name(self):
        settings.crew4_name = " ".join(unicode(self.crew4_name.text()).split())

    def set_crew5_name(self):
        settings.crew5_name = " ".join(unicode(self.crew5_name.text()).split())

    def set_crew6_name(self):
        settings.crew6_name = " ".join(unicode(self.crew6_name.text()).split())

    def set_crew7_name(self):
        settings.crew7_name = " ".join(unicode(self.crew7_name.text()).split())

    def set_crew8_name(self):
        settings.crew8_name = " ".join(unicode(self.crew8_name.text()).split())

    def set_crew9_name(self):
        settings.crew9_name = " ".join(unicode(self.crew9_name.text()).split())

    def set_crew10_name(self):
        settings.crew10_name = " ".join(unicode(self.crew10_name.text()).split())

    def set_crew1_apple_id(self):
        settings.crew1_apple_id = " ".join(unicode(self.crew1_apple_id.text()).split())

    def set_crew2_apple_id(self):
        settings.crew2_apple_id = " ".join(unicode(self.crew2_apple_id.text()).split())

    def set_crew3_apple_id(self):
        settings.crew3_apple_id = " ".join(unicode(self.crew3_apple_id.text()).split())

    def set_crew4_apple_id(self):
        settings.crew4_apple_id = " ".join(unicode(self.crew4_apple_id.text()).split())

    def set_crew5_apple_id(self):
        settings.crew5_apple_id = " ".join(unicode(self.crew5_apple_id.text()).split())

    def set_crew6_apple_id(self):
        settings.crew6_apple_id = " ".join(unicode(self.crew6_apple_id.text()).split())

    def set_crew7_apple_id(self):
        settings.crew7_apple_id = " ".join(unicode(self.crew7_apple_id.text()).split())

    def set_crew8_apple_id(self):
        settings.crew8_apple_id = " ".join(unicode(self.crew8_apple_id.text()).split())

    def set_crew9_apple_id(self):
        settings.crew9_apple_id = " ".join(unicode(self.crew9_apple_id.text()).split())

    def set_crew10_apple_id(self):
        settings.crew10_apple_id = " ".join(unicode(self.crew10_apple_id.text()).split())

    def set_crew1_director(self):
        settings.crew1_director = self.crew1_director.isChecked()
    
    def set_crew1_producer(self):
        settings.crew1_producer = self.crew1_producer.isChecked()
    
    def set_crew1_screenwriter(self):
        settings.crew1_screenwriter = self.crew1_screenwriter.isChecked()
    
    def set_crew1_composer(self):
        settings.crew1_composer = self.crew1_composer.isChecked()
    
    def set_crew1_codirector(self):
        settings.crew1_codirector = self.crew1_codirector.isChecked()

    def set_crew2_director(self):
        settings.crew2_director = self.crew2_director.isChecked()

    def set_crew2_producer(self):
        settings.crew2_producer = self.crew2_producer.isChecked()

    def set_crew2_screenwriter(self):
        settings.crew2_screenwriter = self.crew2_screenwriter.isChecked()

    def set_crew2_composer(self):
        settings.crew2_composer = self.crew2_composer.isChecked()

    def set_crew2_codirector(self):
        settings.crew2_codirector = self.crew2_codirector.isChecked()

    def set_crew3_director(self):
        settings.crew3_director = self.crew3_director.isChecked()

    def set_crew3_producer(self):
        settings.crew3_producer = self.crew3_producer.isChecked()

    def set_crew3_screenwriter(self):
        settings.crew3_screenwriter = self.crew3_screenwriter.isChecked()

    def set_crew3_composer(self):
        settings.crew3_composer = self.crew3_composer.isChecked()

    def set_crew3_codirector(self):
        settings.crew3_codirector = self.crew3_codirector.isChecked()

    def set_crew4_director(self):
        settings.crew4_director = self.crew4_director.isChecked()

    def set_crew4_producer(self):
        settings.crew4_producer = self.crew4_producer.isChecked()

    def set_crew4_screenwriter(self):
        settings.crew4_screenwriter = self.crew4_screenwriter.isChecked()

    def set_crew4_composer(self):
        settings.crew4_composer = self.crew4_composer.isChecked()

    def set_crew4_codirector(self):
        settings.crew4_codirector = self.crew4_codirector.isChecked()

    def set_crew5_director(self):
        settings.crew5_director = self.crew5_director.isChecked()

    def set_crew5_producer(self):
        settings.crew5_producer = self.crew5_producer.isChecked()

    def set_crew5_screenwriter(self):
        settings.crew5_screenwriter = self.crew5_screenwriter.isChecked()

    def set_crew5_composer(self):
        settings.crew5_composer = self.crew5_composer.isChecked()

    def set_crew5_codirector(self):
        settings.crew5_codirector = self.crew5_codirector.isChecked()

    def set_crew6_director(self):
        settings.crew6_director = self.crew6_director.isChecked()

    def set_crew6_producer(self):
        settings.crew6_producer = self.crew6_producer.isChecked()

    def set_crew6_screenwriter(self):
        settings.crew6_screenwriter = self.crew6_screenwriter.isChecked()

    def set_crew6_composer(self):
        settings.crew6_composer = self.crew6_composer.isChecked()

    def set_crew6_codirector(self):
        settings.crew6_codirector = self.crew6_codirector.isChecked()

    def set_crew7_director(self):
        settings.crew7_director = self.crew7_director.isChecked()

    def set_crew7_producer(self):
        settings.crew7_producer = self.crew7_producer.isChecked()

    def set_crew7_screenwriter(self):
        settings.crew7_screenwriter = self.crew7_screenwriter.isChecked()

    def set_crew7_composer(self):
        settings.crew7_composer = self.crew7_composer.isChecked()

    def set_crew7_codirector(self):
        settings.crew7_codirector = self.crew7_codirector.isChecked()

    def set_crew8_director(self):
        settings.crew8_director = self.crew8_director.isChecked()

    def set_crew8_producer(self):
        settings.crew8_producer = self.crew8_producer.isChecked()

    def set_crew8_screenwriter(self):
        settings.crew8_screenwriter = self.crew8_screenwriter.isChecked()

    def set_crew8_composer(self):
        settings.crew8_composer = self.crew8_composer.isChecked()

    def set_crew8_codirector(self):
        settings.crew8_codirector = self.crew8_codirector.isChecked()

    def set_crew9_director(self):
        settings.crew9_director = self.crew9_director.isChecked()

    def set_crew9_producer(self):
        settings.crew9_producer = self.crew9_producer.isChecked()

    def set_crew9_screenwriter(self):
        settings.crew9_screenwriter = self.crew9_screenwriter.isChecked()

    def set_crew9_composer(self):
        settings.crew9_composer = self.crew9_composer.isChecked()

    def set_crew9_codirector(self):
        settings.crew9_codirector = self.crew9_codirector.isChecked()

    def set_crew10_director(self):
        settings.crew10_director = self.crew10_director.isChecked()

    def set_crew10_producer(self):
        settings.crew10_producer = self.crew10_producer.isChecked()

    def set_crew10_screenwriter(self):
        settings.crew10_screenwriter = self.crew10_screenwriter.isChecked()

    def set_crew10_composer(self):
        settings.crew10_composer = self.crew10_composer.isChecked()

    def set_crew10_codirector(self):
        settings.crew10_codirector = self.crew10_codirector.isChecked()

    # feature
    def feature_file_dlg(self):
        settings.feature_file_path = \
            str(QtGui.QFileDialog.getOpenFileName(
                parent=self,
                caption="Locate feature file",
                directory=settings.directory,
                filter="Quicktime files (*.mov)"))

        self.feature_file_lbl.setText(settings.feature_file_path)
        settings.feature_file = os.path.basename(settings.feature_file_path)

        if settings.feature_file_path:
            settings.directory = os.path.dirname(settings.feature_file_path)

    def feature_md5_start(self):
        if settings.feature_file_path == "":
            path_msg = QtGui.QMessageBox()

            path_msg.setIcon(QtGui.QMessageBox.Information)
            path_msg.setText("Please select a feature file.")
            path_msg.setWindowTitle("Input needed")
            path_msg.setStandardButtons(QtGui.QMessageBox.Ok)
            path_msg.exec_()
            return

        else:
            self.feat_md5_stop_btn.setEnabled(True)
            self.feat_md5_start_btn.setEnabled(False)
            self.feat_md5_progress.setRange(0, 0)
            self.tabWidget.tabBar().setTabTextColor(1, QtCore.Qt.red)
            self.connect(self.feat_md5_thread, QtCore.SIGNAL("finished()"), self.feature_md5_done)
            self.feat_md5_thread.start()

    def feature_md5_stop(self):
        self.feat_md5_thread.terminate()
        self.feat_md5_stop_btn.setEnabled(False)
        self.feat_md5_start_btn.setEnabled(True)
        self.tabWidget.tabBar().setTabTextColor(1, QtCore.Qt.black)
        self.feat_md5_progress.setRange(0, 1)
        self.feat_md5_progress.setValue(0)

    def feature_md5_done(self):
        self.feat_md5_stop_btn.setEnabled(False)
        self.feat_md5_start_btn.setEnabled(True)
        self.feat_md5_lbl.setText(settings.feature_md5)
        self.tabWidget.tabBar().setTabTextColor(1, QtCore.Qt.black)
        self.feat_md5_progress.setRange(0, 1)
        self.feat_md5_progress.setValue(1)

    def set_feat_md5_lbl(self):
        feat_md5_clean = " ".join(unicode(self.feat_md5_lbl.text()).split())
        settings.feature_md5 = feat_md5_clean

    def set_feat_audio(self):
        settings.feature_audio = str(self.comboFeatureAudio.currentText()).split(":", 1)[0]

    def set_feat_top_crop(self):
        settings.feat_crop_top = " ".join(unicode(self.feat_top_crop.text()).split())

    def set_feat_bottom_crop(self):
        settings.feat_crop_bottom = " ".join(unicode(self.feat_bottom_crop.text()).split())

    def set_feat_left_crop(self):
        settings.feat_crop_left = " ".join(unicode(self.feat_left_crop.text()).split())

    def set_feat_right_crop(self):
        settings.feat_crop_right = " ".join(unicode(self.feat_right_crop.text()).split())

    def check_feat_narr(self):
        settings.feat_check_narr = self.feat_narratives.isChecked()
        self.comboNarrFeature.setEnabled(self.feat_narratives.isChecked())

    def set_narr_feat(self):
        settings.narr_feat = str(self.comboNarrFeature.currentText()).split(":", 1)[0]

    def check_feat_subs(self):
        settings.feat_check_subs = self.feat_subs.isChecked()
        self.comboSubFeature.setEnabled(self.feat_subs.isChecked())

    def set_sub_feat(self):
        settings.sub_feat = str(self.comboSubFeature.currentText()).split(":", 1)[0]

    # chapters
    def set_timecode_format(self):
        settings.tc_format = str(self.tc_format.currentText())

        index_tc_format_ww = self.tc_format_ww_trailer.findText(settings.tc_format, QtCore.Qt.MatchFixedString)
        self.tc_format_ww_trailer.setCurrentIndex(index_tc_format_ww)

        index_tc_format_loc = self.tc_format_loc_trailer.findText(settings.tc_format, QtCore.Qt.MatchFixedString)
        self.tc_format_loc_trailer.setCurrentIndex(index_tc_format_loc)

    def chap_locale_add(self):
        box = QtGui.QComboBox(self)
        box.addItems(self.list_of_languages)
        box.setObjectName("chapter_locale%d" % self.chapter_locale_count)
        box.currentIndexChanged.connect(self.set_chapter_locales)
        index_chapter_locale = box.findText("en-US: English (United States)", QtCore.Qt.MatchFixedString)
        box.setCurrentIndex(index_chapter_locale)

        self.chapter_title_lyt.addWidget(box, 0, self.chapter_locale_count)

        self.chapter_locale_count = len(settings.chapter_locales.keys())

    def chap_locale_del(self):
        if self.chapter_title_lyt.count() > 0:
            to_delete = self.chapter_title_lyt.takeAt(self.chapter_title_lyt.count() - 1)

            widget = to_delete.widget()
            if widget:
                widget.deleteLater()

        if len(settings.chapter_locales.keys()) > 0:
            settings.chapter_locales.pop(settings.chapter_locales.keys()[-1])

        self.chapter_locale_count = len(settings.chapter_locales.keys())

    def set_chapter_locales(self):
        sender = self.sender()

        settings.chapter_locales.update({str(sender.objectName()): str(sender.currentText())})

    def set_chap_01_tc(self):
        settings.chapters_tc["01"] = str(self.chap_01_tc_ln.text())

    def set_chap_02_tc(self):
        settings.chapters_tc["02"] = str(self.chap_02_tc_ln.text())

    def set_chap_03_tc(self):
        settings.chapters_tc["03"] = str(self.chap_03_tc_ln.text())

    def set_chap_04_tc(self):
        settings.chapters_tc["04"] = str(self.chap_04_tc_ln.text())

    def set_chap_05_tc(self):
        settings.chapters_tc["05"] = str(self.chap_05_tc_ln.text())

    def set_chap_06_tc(self):
        settings.chapters_tc["06"] = str(self.chap_06_tc_ln.text())

    def set_chap_07_tc(self):
        settings.chapters_tc["07"] = str(self.chap_07_tc_ln.text())

    def set_chap_08_tc(self):
        settings.chapters_tc["08"] = str(self.chap_08_tc_ln.text())

    def set_chap_09_tc(self):
        settings.chapters_tc["09"] = str(self.chap_09_tc_ln.text())

    def set_chap_10_tc(self):
        settings.chapters_tc["10"] = str(self.chap_10_tc_ln.text())

    def set_chap_11_tc(self):
        settings.chapters_tc["11"] = str(self.chap_11_tc_ln.text())

    def set_chap_12_tc(self):
        settings.chapters_tc["12"] = str(self.chap_12_tc_ln.text())

    def set_chap_13_tc(self):
        settings.chapters_tc["13"] = str(self.chap_13_tc_ln.text())

    def set_chap_14_tc(self):
        settings.chapters_tc["14"] = str(self.chap_14_tc_ln.text())

    def set_chap_15_tc(self):
        settings.chapters_tc["15"] = str(self.chap_15_tc_ln.text())

    def set_chap_16_tc(self):
        settings.chapters_tc["16"] = str(self.chap_16_tc_ln.text())

    def set_chap_17_tc(self):
        settings.chapters_tc["17"] = str(self.chap_17_tc_ln.text())

    def set_chap_18_tc(self):
        settings.chapters_tc["18"] = str(self.chap_18_tc_ln.text())

    def set_chap_19_tc(self):
        settings.chapters_tc["19"] = str(self.chap_19_tc_ln.text())

    def set_chap_20_tc(self):
        settings.chapters_tc["20"] = str(self.chap_20_tc_ln.text())

    def set_chap_01_thumb_tc(self):
        settings.thumbs_tc["01"] = str(self.chap_01_thumb_tc_ln.text())

    def set_chap_02_thumb_tc(self):
        settings.thumbs_tc["02"] = str(self.chap_02_thumb_tc_ln.text())

    def set_chap_03_thumb_tc(self):
        settings.thumbs_tc["03"] = str(self.chap_03_thumb_tc_ln.text())

    def set_chap_04_thumb_tc(self):
        settings.thumbs_tc["04"] = str(self.chap_04_thumb_tc_ln.text())

    def set_chap_05_thumb_tc(self):
        settings.thumbs_tc["05"] = str(self.chap_05_thumb_tc_ln.text())

    def set_chap_06_thumb_tc(self):
        settings.thumbs_tc["06"] = str(self.chap_06_thumb_tc_ln.text())

    def set_chap_07_thumb_tc(self):
        settings.thumbs_tc["07"] = str(self.chap_07_thumb_tc_ln.text())

    def set_chap_08_thumb_tc(self):
        settings.thumbs_tc["08"] = str(self.chap_08_thumb_tc_ln.text())

    def set_chap_09_thumb_tc(self):
        settings.thumbs_tc["09"] = str(self.chap_09_thumb_tc_ln.text())

    def set_chap_10_thumb_tc(self):
        settings.thumbs_tc["10"] = str(self.chap_10_thumb_tc_ln.text())

    def set_chap_11_thumb_tc(self):
        settings.thumbs_tc["11"] = str(self.chap_11_thumb_tc_ln.text())

    def set_chap_12_thumb_tc(self):
        settings.thumbs_tc["12"] = str(self.chap_12_thumb_tc_ln.text())

    def set_chap_13_thumb_tc(self):
        settings.thumbs_tc["13"] = str(self.chap_13_thumb_tc_ln.text())

    def set_chap_14_thumb_tc(self):
        settings.thumbs_tc["14"] = str(self.chap_14_thumb_tc_ln.text())

    def set_chap_15_thumb_tc(self):
        settings.thumbs_tc["15"] = str(self.chap_15_thumb_tc_ln.text())

    def set_chap_16_thumb_tc(self):
        settings.thumbs_tc["16"] = str(self.chap_16_thumb_tc_ln.text())

    def set_chap_17_thumb_tc(self):
        settings.thumbs_tc["17"] = str(self.chap_17_thumb_tc_ln.text())

    def set_chap_18_thumb_tc(self):
        settings.thumbs_tc["18"] = str(self.chap_18_thumb_tc_ln.text())

    def set_chap_19_thumb_tc(self):
        settings.thumbs_tc["19"] = str(self.chap_19_thumb_tc_ln.text())

    def set_chap_20_thumb_tc(self):
        settings.thumbs_tc["20"] = str(self.chap_20_thumb_tc_ln.text())

    # trailer
    def trailer_file_dlg(self):
        settings.trailer_file_path = \
            str(QtGui.QFileDialog.getOpenFileName(
                parent=self,
                caption="Locate trailer file",
                directory=settings.directory,
                filter="Quicktime files (*.mov)"))

        self.trailer_file_lbl.setText(settings.trailer_file_path)

        if settings.trailer_file_path:
            settings.directory = os.path.dirname(settings.trailer_file_path)

    def trailer_md5_start(self):
        if settings.trailer_file_path == "":
            path_msg = QtGui.QMessageBox()

            path_msg.setIcon(QtGui.QMessageBox.Information)
            path_msg.setText("Please select a trailer file.")
            path_msg.setWindowTitle("Input needed")
            path_msg.setStandardButtons(QtGui.QMessageBox.Ok)
            path_msg.exec_()
            return

        else:
            self.trailer_md5_stop_btn.setEnabled(True)
            self.trailer_md5_start_btn.setEnabled(False)
            self.trailer_md5_progress.setRange(0, 0)
            self.tabWidget.tabBar().setTabTextColor(4, QtCore.Qt.red)
            self.connect(self.trailer_md5_thread, QtCore.SIGNAL("finished()"), self.trailer_md5_done)
            self.trailer_md5_thread.start()

    def trailer_md5_stop(self):
        self.trailer_md5_thread.terminate()
        self.trailer_md5_stop_btn.setEnabled(False)
        self.trailer_md5_start_btn.setEnabled(True)
        self.tabWidget.tabBar().setTabTextColor(4, QtCore.Qt.black)
        self.trailer_md5_progress.setRange(0, 1)
        self.trailer_md5_progress.setValue(0)

    def trailer_md5_done(self):
        self.trailer_md5_stop_btn.setEnabled(False)
        self.trailer_md5_start_btn.setEnabled(True)
        self.trailer_md5_lbl.setText(settings.trailer_md5)
        self.tabWidget.tabBar().setTabTextColor(4, QtCore.Qt.black)
        self.trailer_md5_progress.setRange(0, 1)
        self.trailer_md5_progress.setValue(1)

    def set_trailer_md5_lbl(self):
        trailer_md5_clean = " ".join(unicode(self.trailer_md5_lbl.text()).split())
        settings.trailer_md5 = trailer_md5_clean

    def set_trailer_still_tc(self):
        settings.trailer_still = " ".join(unicode(self.trailer_still_tc.text()).split())

    def set_trailer_tc_format(self):
        settings.trailer_tc = str(self.tc_format_ww_trailer.currentText())

    def set_trailer_audio(self):
        settings.trailer_audio = str(self.comboTrailerAudio.currentText()).split(":", 1)[0]

    def set_trailer_top_crop(self):
        settings.trailer_crop_top = " ".join(unicode(self.trailer_top_crop.text()).split())

    def set_trailer_bottom_crop(self):
        settings.trailer_crop_bottom = " ".join(unicode(self.trailer_bottom_crop.text()).split())

    def set_trailer_left_crop(self):
        settings.trailer_crop_left = " ".join(unicode(self.trailer_left_crop.text()).split())

    def set_trailer_right_crop(self):
        settings.trailer_crop_right = " ".join(unicode(self.trailer_right_crop.text()).split())

    def check_trailer_narr(self):
        settings.trailer_check_narr = self.trailer_narr.isChecked()
        self.comboNarrTrailer.setEnabled(self.trailer_narr.isChecked())

    def set_narr_trailer(self):
        settings.narr_trailer = str(self.comboNarrTrailer.currentText()).split(":", 1)[0]

    def check_trailer_subs(self):
        settings.trailer_check_subs = self.trailer_subs.isChecked()
        self.comboSubTrailer.setEnabled(self.trailer_subs.isChecked())

    def set_sub_trailer(self):
        settings.sub_trailer = str(self.comboSubTrailer.currentText()).split(":", 1)[0]

    # feature assets
    def feat_asset1_dlg(self):
        settings.feat_asset1_path = \
            str(QtGui.QFileDialog.getOpenFileName(
                parent=self,
                caption="Locate asset file",
                directory=settings.directory))

        self.feat_asset1_lbl.setText(os.path.basename(settings.feat_asset1_path))

        if settings.feat_asset1_path:
            settings.directory = os.path.dirname(settings.feat_asset1_path)

    def feat_asset2_dlg(self):
        settings.feat_asset2_path = \
            str(QtGui.QFileDialog.getOpenFileName(
                parent=self,
                caption="Locate asset file",
                directory=settings.directory))

        self.feat_asset2_lbl.setText(os.path.basename(settings.feat_asset2_path))

        if settings.feat_asset2_path:
            settings.directory = os.path.dirname(settings.feat_asset2_path)

    def feat_asset3_dlg(self):
        settings.feat_asset3_path = \
            str(QtGui.QFileDialog.getOpenFileName(
                parent=self,
                caption="Locate asset file",
                directory=settings.directory))

        self.feat_asset3_lbl.setText(os.path.basename(settings.feat_asset3_path))

        if settings.feat_asset3_path:
            settings.directory = os.path.dirname(settings.feat_asset3_path)

    def feat_asset4_dlg(self):
        settings.feat_asset4_path = \
            str(QtGui.QFileDialog.getOpenFileName(
                parent=self,
                caption="Locate asset file",
                directory=settings.directory))

        self.feat_asset4_lbl.setText(os.path.basename(settings.feat_asset4_path))

        if settings.feat_asset4_path:
            settings.directory = os.path.dirname(settings.feat_asset4_path)

    def feat_asset5_dlg(self):
        settings.feat_asset5_path = \
            str(QtGui.QFileDialog.getOpenFileName(
                parent=self,
                caption="Locate asset file",
                directory=settings.directory))

        self.feat_asset5_lbl.setText(os.path.basename(settings.feat_asset5_path))

        if settings.feat_asset5_path:
            settings.directory = os.path.dirname(settings.feat_asset5_path)

    def feat_asset6_dlg(self):
        settings.feat_asset6_path = \
            str(QtGui.QFileDialog.getOpenFileName(
                parent=self,
                caption="Locate asset file",
                directory=settings.directory))

        self.feat_asset6_lbl.setText(os.path.basename(settings.feat_asset6_path))

        if settings.feat_asset6_path:
            settings.directory = os.path.dirname(settings.feat_asset6_path)

    def feat_asset7_dlg(self):
        settings.feat_asset7_path = \
            str(QtGui.QFileDialog.getOpenFileName(
                parent=self,
                caption="Locate asset file",
                directory=settings.directory))

        self.feat_asset7_lbl.setText(os.path.basename(settings.feat_asset7_path))

        if settings.feat_asset7_path:
            settings.directory = os.path.dirname(settings.feat_asset7_path)

    def feat_asset8_dlg(self):
        settings.feat_asset8_path = \
            str(QtGui.QFileDialog.getOpenFileName(
                parent=self,
                caption="Locate asset file",
                directory=settings.directory))

        self.feat_asset8_lbl.setText(os.path.basename(settings.feat_asset8_path))

        if settings.feat_asset8_path:
            settings.directory = os.path.dirname(settings.feat_asset8_path)

    def set_feat_asset1_role(self):
        settings.feat_asset1_role = str(self.feat_asset1_role.currentText())

        if settings.feat_asset1_role != "notes":
            self.feat_asset1_locale.setEnabled(True)

        else:
            self.feat_asset1_locale.setEnabled(False)

        if settings.feat_asset1_role == "notes" \
                or settings.feat_asset1_role == "captions" \
                or settings.feat_asset1_role == "video.end.dub_credits" \
                or settings.feat_asset1_role == "forced_subtitles" \
                or settings.feat_asset1_role == "audio.visually_impaired" \
                or settings.feat_asset1_role == "subtitles.hearing_impaired":
            self.feat_asset1_add_terr.setEnabled(False)
            self.feat_asset1_del_terr.setEnabled(False)

        else:
            self.feat_asset1_add_terr.setEnabled(True)
            self.feat_asset1_del_terr.setEnabled(True)

    def set_feat_asset1_locale(self):
        settings.feat_asset1_locale = str(self.feat_asset1_locale.currentText()).split(":", 1)[0]

    def set_feat_asset2_role(self):
        settings.feat_asset2_role = str(self.feat_asset2_role.currentText())

        if settings.feat_asset2_role != "notes":
            self.feat_asset2_locale.setEnabled(True)

        else:
            self.feat_asset2_locale.setEnabled(False)

        if settings.feat_asset2_role == "notes" \
                or settings.feat_asset2_role == "captions" \
                or settings.feat_asset2_role == "video.end.dub_credits" \
                or settings.feat_asset2_role == "forced_subtitles" \
                or settings.feat_asset2_role == "audio.visually_impaired" \
                or settings.feat_asset2_role == "subtitles.hearing_impaired":
            self.feat_asset2_add_terr.setEnabled(False)
            self.feat_asset2_del_terr.setEnabled(False)

        else:
            self.feat_asset2_add_terr.setEnabled(True)
            self.feat_asset2_del_terr.setEnabled(True)

    def set_feat_asset2_locale(self):
        settings.feat_asset2_locale = str(self.feat_asset2_locale.currentText()).split(":", 1)[0]

    def set_feat_asset3_role(self):
        settings.feat_asset3_role = str(self.feat_asset3_role.currentText())

        if settings.feat_asset3_role != "notes":
            self.feat_asset3_locale.setEnabled(True)

        else:
            self.feat_asset3_locale.setEnabled(False)

        if settings.feat_asset3_role == "notes" \
                or settings.feat_asset3_role == "captions" \
                or settings.feat_asset3_role == "video.end.dub_credits" \
                or settings.feat_asset3_role == "forced_subtitles" \
                or settings.feat_asset3_role == "audio.visually_impaired" \
                or settings.feat_asset3_role == "subtitles.hearing_impaired":
            self.feat_asset3_add_terr.setEnabled(False)
            self.feat_asset3_del_terr.setEnabled(False)

        else:
            self.feat_asset3_add_terr.setEnabled(True)
            self.feat_asset3_del_terr.setEnabled(True)

    def set_feat_asset3_locale(self):
        settings.feat_asset3_locale = str(self.feat_asset3_locale.currentText()).split(":", 1)[0]

    def set_feat_asset4_role(self):
        settings.feat_asset4_role = str(self.feat_asset4_role.currentText())

        if settings.feat_asset4_role != "notes":
            self.feat_asset4_locale.setEnabled(True)

        else:
            self.feat_asset4_locale.setEnabled(False)

        if settings.feat_asset4_role == "notes" \
                or settings.feat_asset4_role == "captions" \
                or settings.feat_asset4_role == "video.end.dub_credits" \
                or settings.feat_asset4_role == "forced_subtitles" \
                or settings.feat_asset4_role == "audio.visually_impaired" \
                or settings.feat_asset4_role == "subtitles.hearing_impaired":
            self.feat_asset4_add_terr.setEnabled(False)
            self.feat_asset4_del_terr.setEnabled(False)

        else:
            self.feat_asset4_add_terr.setEnabled(True)
            self.feat_asset4_del_terr.setEnabled(True)

    def set_feat_asset4_locale(self):
        settings.feat_asset4_locale = str(self.feat_asset4_locale.currentText()).split(":", 1)[0]

    def set_feat_asset5_role(self):
        settings.feat_asset5_role = str(self.feat_asset5_role.currentText())

        if settings.feat_asset5_role != "notes":
            self.feat_asset5_locale.setEnabled(True)

        else:
            self.feat_asset5_locale.setEnabled(False)

        if settings.feat_asset5_role == "notes" \
                or settings.feat_asset5_role == "captions" \
                or settings.feat_asset5_role == "video.end.dub_credits" \
                or settings.feat_asset5_role == "forced_subtitles" \
                or settings.feat_asset5_role == "audio.visually_impaired" \
                or settings.feat_asset5_role == "subtitles.hearing_impaired":
            self.feat_asset5_add_terr.setEnabled(False)
            self.feat_asset5_del_terr.setEnabled(False)

        else:
            self.feat_asset5_add_terr.setEnabled(True)
            self.feat_asset5_del_terr.setEnabled(True)

    def set_feat_asset5_locale(self):
        settings.feat_asset5_locale = str(self.feat_asset5_locale.currentText()).split(":", 1)[0]

    def set_feat_asset6_role(self):
        settings.feat_asset6_role = str(self.feat_asset6_role.currentText())

        if settings.feat_asset6_role != "notes":
            self.feat_asset6_locale.setEnabled(True)

        else:
            self.feat_asset6_locale.setEnabled(False)

        if settings.feat_asset6_role == "notes" \
                or settings.feat_asset6_role == "captions" \
                or settings.feat_asset6_role == "video.end.dub_credits" \
                or settings.feat_asset6_role == "forced_subtitles" \
                or settings.feat_asset6_role == "audio.visually_impaired" \
                or settings.feat_asset6_role == "subtitles.hearing_impaired":
            self.feat_asset6_add_terr.setEnabled(False)
            self.feat_asset6_del_terr.setEnabled(False)

        else:
            self.feat_asset6_add_terr.setEnabled(True)
            self.feat_asset6_del_terr.setEnabled(True)

    def set_feat_asset6_locale(self):
        settings.feat_asset6_locale = str(self.feat_asset6_locale.currentText()).split(":", 1)[0]

    def set_feat_asset7_role(self):
        settings.feat_asset7_role = str(self.feat_asset7_role.currentText())

        if settings.feat_asset7_role != "notes":
            self.feat_asset7_locale.setEnabled(True)

        else:
            self.feat_asset7_locale.setEnabled(False)

        if settings.feat_asset7_role == "notes" \
                or settings.feat_asset7_role == "captions" \
                or settings.feat_asset7_role == "video.end.dub_credits" \
                or settings.feat_asset7_role == "forced_subtitles" \
                or settings.feat_asset7_role == "audio.visually_impaired" \
                or settings.feat_asset7_role == "subtitles.hearing_impaired":
            self.feat_asset7_add_terr.setEnabled(False)
            self.feat_asset7_del_terr.setEnabled(False)

        else:
            self.feat_asset7_add_terr.setEnabled(True)
            self.feat_asset7_del_terr.setEnabled(True)

    def set_feat_asset7_locale(self):
        settings.feat_asset7_locale = str(self.feat_asset7_locale.currentText()).split(":", 1)[0]

    def set_feat_asset8_role(self):
        settings.feat_asset8_role = str(self.feat_asset8_role.currentText())

        if settings.feat_asset8_role != "notes":
            self.feat_asset8_locale.setEnabled(True)

        else:
            self.feat_asset8_locale.setEnabled(False)

        if settings.feat_asset8_role == "notes" \
                or settings.feat_asset8_role == "captions" \
                or settings.feat_asset8_role == "video.end.dub_credits" \
                or settings.feat_asset8_role == "forced_subtitles" \
                or settings.feat_asset8_role == "audio.visually_impaired" \
                or settings.feat_asset8_role == "subtitles.hearing_impaired":
            self.feat_asset8_add_terr.setEnabled(False)
            self.feat_asset8_del_terr.setEnabled(False)

        else:
            self.feat_asset8_add_terr.setEnabled(True)
            self.feat_asset8_del_terr.setEnabled(True)

    def set_feat_asset8_locale(self):
        settings.feat_asset8_locale = str(self.feat_asset8_locale.currentText()).split(":", 1)[0]

    def feat_asset1_add(self):
        box = QtGui.QComboBox(self)
        box.addItems(self.country_values)
        box.setObjectName("territory%d" % self.feat_asset1_count)
        box.currentIndexChanged.connect(self.set_feat_asset1_terr)
        index_feat_asset1_territories = box.findText("CA", QtCore.Qt.MatchFixedString)
        box.setCurrentIndex(index_feat_asset1_territories)

        self.feat_asset1_lyt.addWidget(box, 0, self.feat_asset1_count)

        self.feat_asset1_count = len(settings.feat_asset1_territories.keys())

    def feat_asset1_del(self):
        if self.feat_asset1_lyt.count() > 0:
            to_delete = self.feat_asset1_lyt.takeAt(self.feat_asset1_lyt.count() - 1)

            widget = to_delete.widget()
            if widget:
                widget.deleteLater()

        if len(settings.feat_asset1_territories.keys()) > 0:
            settings.feat_asset1_territories.pop(settings.feat_asset1_territories.keys()[-1])

        self.feat_asset1_count = len(settings.feat_asset1_territories.keys())

    def set_feat_asset1_terr(self):
        sender = self.sender()

        settings.feat_asset1_territories.update({str(sender.objectName()): str(sender.currentText())})

    def feat_asset2_add(self):
        box = QtGui.QComboBox(self)
        box.addItems(self.country_values)
        box.setObjectName("territory%d" % self.feat_asset2_count)
        box.currentIndexChanged.connect(self.set_feat_asset2_terr)
        index_feat_asset2_territories = box.findText("CA", QtCore.Qt.MatchFixedString)
        box.setCurrentIndex(index_feat_asset2_territories)

        self.feat_asset2_lyt.addWidget(box, 0, self.feat_asset2_count)

        self.feat_asset2_count = len(settings.feat_asset2_territories.keys())

    def feat_asset2_del(self):
        if self.feat_asset2_lyt.count() > 0:
            to_delete = self.feat_asset2_lyt.takeAt(self.feat_asset2_lyt.count() - 1)

            widget = to_delete.widget()
            if widget:
                widget.deleteLater()

        if len(settings.feat_asset2_territories.keys()) > 0:
            settings.feat_asset2_territories.pop(settings.feat_asset2_territories.keys()[-1])

        self.feat_asset2_count = len(settings.feat_asset2_territories.keys())

    def set_feat_asset2_terr(self):
        sender = self.sender()

        settings.feat_asset2_territories.update({str(sender.objectName()): str(sender.currentText())})

    def feat_asset3_add(self):
        box = QtGui.QComboBox(self)
        box.addItems(self.country_values)
        box.setObjectName("territory%d" % self.feat_asset3_count)
        box.currentIndexChanged.connect(self.set_feat_asset3_terr)
        index_feat_asset3_territories = box.findText("CA", QtCore.Qt.MatchFixedString)
        box.setCurrentIndex(index_feat_asset3_territories)

        self.feat_asset3_lyt.addWidget(box, 0, self.feat_asset3_count)

        self.feat_asset3_count = len(settings.feat_asset3_territories.keys())

    def feat_asset3_del(self):
        if self.feat_asset3_lyt.count() > 0:
            to_delete = self.feat_asset3_lyt.takeAt(self.feat_asset3_lyt.count() - 1)

            widget = to_delete.widget()
            if widget:
                widget.deleteLater()

        if len(settings.feat_asset3_territories.keys()) > 0:
            settings.feat_asset3_territories.pop(settings.feat_asset3_territories.keys()[-1])

        self.feat_asset3_count = len(settings.feat_asset3_territories.keys())

    def set_feat_asset3_terr(self):
        sender = self.sender()

        settings.feat_asset3_territories.update({str(sender.objectName()): str(sender.currentText())})

    def feat_asset4_add(self):
        box = QtGui.QComboBox(self)
        box.addItems(self.country_values)
        box.setObjectName("territory%d" % self.feat_asset4_count)
        box.currentIndexChanged.connect(self.set_feat_asset4_terr)
        index_feat_asset4_territories = box.findText("CA", QtCore.Qt.MatchFixedString)
        box.setCurrentIndex(index_feat_asset4_territories)

        self.feat_asset4_lyt.addWidget(box, 0, self.feat_asset4_count)

        self.feat_asset4_count = len(settings.feat_asset4_territories.keys())

    def feat_asset4_del(self):
        if self.feat_asset4_lyt.count() > 0:
            to_delete = self.feat_asset4_lyt.takeAt(self.feat_asset4_lyt.count() - 1)

            widget = to_delete.widget()
            if widget:
                widget.deleteLater()

        if len(settings.feat_asset4_territories.keys()) > 0:
            settings.feat_asset4_territories.pop(settings.feat_asset4_territories.keys()[-1])

        self.feat_asset4_count = len(settings.feat_asset4_territories.keys())

    def set_feat_asset4_terr(self):
        sender = self.sender()

        settings.feat_asset4_territories.update({str(sender.objectName()): str(sender.currentText())})

    def feat_asset5_add(self):
        box = QtGui.QComboBox(self)
        box.addItems(self.country_values)
        box.setObjectName("territory%d" % self.feat_asset5_count)
        box.currentIndexChanged.connect(self.set_feat_asset5_terr)
        index_feat_asset5_territories = box.findText("CA", QtCore.Qt.MatchFixedString)
        box.setCurrentIndex(index_feat_asset5_territories)

        self.feat_asset5_lyt.addWidget(box, 0, self.feat_asset5_count)

        self.feat_asset5_count = len(settings.feat_asset5_territories.keys())

    def feat_asset5_del(self):
        if self.feat_asset5_lyt.count() > 0:
            to_delete = self.feat_asset5_lyt.takeAt(self.feat_asset5_lyt.count() - 1)

            widget = to_delete.widget()
            if widget:
                widget.deleteLater()

        if len(settings.feat_asset5_territories.keys()) > 0:
            settings.feat_asset5_territories.pop(settings.feat_asset5_territories.keys()[-1])

        self.feat_asset5_count = len(settings.feat_asset5_territories.keys())

    def set_feat_asset5_terr(self):
        sender = self.sender()

        settings.feat_asset5_territories.update({str(sender.objectName()): str(sender.currentText())})

    def feat_asset6_add(self):
        box = QtGui.QComboBox(self)
        box.addItems(self.country_values)
        box.setObjectName("territory%d" % self.feat_asset6_count)
        box.currentIndexChanged.connect(self.set_feat_asset6_terr)
        index_feat_asset6_territories = box.findText("CA", QtCore.Qt.MatchFixedString)
        box.setCurrentIndex(index_feat_asset6_territories)

        self.feat_asset6_lyt.addWidget(box, 0, self.feat_asset6_count)

        self.feat_asset6_count = len(settings.feat_asset6_territories.keys())

    def feat_asset6_del(self):
        if self.feat_asset6_lyt.count() > 0:
            to_delete = self.feat_asset6_lyt.takeAt(self.feat_asset6_lyt.count() - 1)

            widget = to_delete.widget()
            if widget:
                widget.deleteLater()

        if len(settings.feat_asset6_territories.keys()) > 0:
            settings.feat_asset6_territories.pop(settings.feat_asset6_territories.keys()[-1])

        self.feat_asset6_count = len(settings.feat_asset6_territories.keys())

    def set_feat_asset6_terr(self):
        sender = self.sender()

        settings.feat_asset6_territories.update({str(sender.objectName()): str(sender.currentText())})

    def feat_asset7_add(self):
        box = QtGui.QComboBox(self)
        box.addItems(self.country_values)
        box.setObjectName("territory%d" % self.feat_asset7_count)
        box.currentIndexChanged.connect(self.set_feat_asset7_terr)
        index_feat_asset7_territories = box.findText("CA", QtCore.Qt.MatchFixedString)
        box.setCurrentIndex(index_feat_asset7_territories)

        self.feat_asset7_lyt.addWidget(box, 0, self.feat_asset7_count)

        self.feat_asset7_count = len(settings.feat_asset7_territories.keys())

    def feat_asset7_del(self):
        if self.feat_asset7_lyt.count() > 0:
            to_delete = self.feat_asset7_lyt.takeAt(self.feat_asset7_lyt.count() - 1)

            widget = to_delete.widget()
            if widget:
                widget.deleteLater()

        if len(settings.feat_asset7_territories.keys()) > 0:
            settings.feat_asset7_territories.pop(settings.feat_asset7_territories.keys()[-1])

        self.feat_asset7_count = len(settings.feat_asset7_territories.keys())

    def set_feat_asset7_terr(self):
        sender = self.sender()

        settings.feat_asset7_territories.update({str(sender.objectName()): str(sender.currentText())})

    def feat_asset8_add(self):
        box = QtGui.QComboBox(self)
        box.addItems(self.country_values)
        box.setObjectName("territory%d" % self.feat_asset8_count)
        box.currentIndexChanged.connect(self.set_feat_asset8_terr)
        index_feat_asset8_territories = box.findText("CA", QtCore.Qt.MatchFixedString)
        box.setCurrentIndex(index_feat_asset8_territories)

        self.feat_asset8_lyt.addWidget(box, 0, self.feat_asset8_count)

        self.feat_asset8_count = len(settings.feat_asset8_territories.keys())

    def feat_asset8_del(self):
        if self.feat_asset8_lyt.count() > 0:
            to_delete = self.feat_asset8_lyt.takeAt(self.feat_asset8_lyt.count() - 1)

            widget = to_delete.widget()
            if widget:
                widget.deleteLater()

        if len(settings.feat_asset8_territories.keys()) > 0:
            settings.feat_asset8_territories.pop(settings.feat_asset8_territories.keys()[-1])

        self.feat_asset8_count = len(settings.feat_asset8_territories.keys())

    def set_feat_asset8_terr(self):
        sender = self.sender()

        settings.feat_asset8_territories.update({str(sender.objectName()): str(sender.currentText())})

    # trailer assets
    def trailer_asset1_dlg(self):
        settings.trailer_asset1_path = \
            str(QtGui.QFileDialog.getOpenFileName(
                parent=self,
                caption="Locate asset file",
                directory=settings.directory))

        self.trailer_asset1_lbl.setText(os.path.basename(settings.trailer_asset1_path))

        if settings.trailer_asset1_path:
            settings.directory = os.path.dirname(settings.trailer_asset1_path)

    def trailer_asset2_dlg(self):
        settings.trailer_asset2_path = \
            str(QtGui.QFileDialog.getOpenFileName(
                parent=self,
                caption="Locate asset file",
                directory=settings.directory))

        self.trailer_asset2_lbl.setText(os.path.basename(settings.trailer_asset2_path))

        if settings.trailer_asset2_path:
            settings.directory = os.path.dirname(settings.trailer_asset2_path)

    def trailer_asset3_dlg(self):
        settings.trailer_asset3_path = \
            str(QtGui.QFileDialog.getOpenFileName(
                parent=self,
                caption="Locate asset file",
                directory=settings.directory))

        self.trailer_asset3_lbl.setText(os.path.basename(settings.trailer_asset3_path))

        if settings.trailer_asset3_path:
            settings.directory = os.path.dirname(settings.trailer_asset3_path)

    def trailer_asset4_dlg(self):
        settings.trailer_asset4_path = \
            str(QtGui.QFileDialog.getOpenFileName(
                parent=self,
                caption="Locate asset file",
                directory=settings.directory))

        self.trailer_asset4_lbl.setText(os.path.basename(settings.trailer_asset4_path))

        if settings.trailer_asset4_path:
            settings.directory = os.path.dirname(settings.trailer_asset4_path)

    def trailer_asset5_dlg(self):
        settings.trailer_asset5_path = \
            str(QtGui.QFileDialog.getOpenFileName(
                parent=self,
                caption="Locate asset file",
                directory=settings.directory))

        self.trailer_asset5_lbl.setText(os.path.basename(settings.trailer_asset5_path))

        if settings.trailer_asset5_path:
            settings.directory = os.path.dirname(settings.trailer_asset5_path)

    def trailer_asset6_dlg(self):
        settings.trailer_asset6_path = \
            str(QtGui.QFileDialog.getOpenFileName(
                parent=self,
                caption="Locate asset file",
                directory=settings.directory))

        self.trailer_asset6_lbl.setText(os.path.basename(settings.trailer_asset6_path))

        if settings.trailer_asset6_path:
            settings.directory = os.path.dirname(settings.trailer_asset6_path)

    def trailer_asset7_dlg(self):
        settings.trailer_asset7_path = \
            str(QtGui.QFileDialog.getOpenFileName(
                parent=self,
                caption="Locate asset file",
                directory=settings.directory))

        self.trailer_asset7_lbl.setText(os.path.basename(settings.trailer_asset7_path))

        if settings.trailer_asset7_path:
            settings.directory = os.path.dirname(settings.trailer_asset7_path)

    def trailer_asset8_dlg(self):
        settings.trailer_asset8_path = \
            str(QtGui.QFileDialog.getOpenFileName(
                parent=self,
                caption="Locate asset file",
                directory=settings.directory))

        self.trailer_asset8_lbl.setText(os.path.basename(settings.trailer_asset8_path))

        if settings.trailer_asset8_path:
            settings.directory = os.path.dirname(settings.trailer_asset8_path)

    def set_trailer_asset1_role(self):
        settings.trailer_asset1_role = str(self.trailer_asset1_role.currentText())

        if settings.trailer_asset1_role != "notes":
            self.trailer_asset1_locale.setEnabled(True)

        else:
            self.trailer_asset1_locale.setEnabled(False)

    def set_trailer_asset1_locale(self):
        settings.trailer_asset1_locale = str(self.trailer_asset1_locale.currentText()).split(":", 1)[0]

    def set_trailer_asset2_role(self):
        settings.trailer_asset2_role = str(self.trailer_asset2_role.currentText())

        if settings.trailer_asset2_role != "notes":
            self.trailer_asset2_locale.setEnabled(True)

        else:
            self.trailer_asset2_locale.setEnabled(False)

    def set_trailer_asset2_locale(self):
        settings.trailer_asset2_locale = str(self.trailer_asset2_locale.currentText()).split(":", 1)[0]

    def set_trailer_asset3_role(self):
        settings.trailer_asset3_role = str(self.trailer_asset3_role.currentText())

        if settings.trailer_asset3_role != "notes":
            self.trailer_asset3_locale.setEnabled(True)

        else:
            self.trailer_asset3_locale.setEnabled(False)

    def set_trailer_asset3_locale(self):
        settings.trailer_asset3_locale = str(self.trailer_asset3_locale.currentText()).split(":", 1)[0]

    def set_trailer_asset4_role(self):
        settings.trailer_asset4_role = str(self.trailer_asset4_role.currentText())

        if settings.trailer_asset4_role != "notes":
            self.trailer_asset4_locale.setEnabled(True)

        else:
            self.trailer_asset4_locale.setEnabled(False)

    def set_trailer_asset4_locale(self):
        settings.trailer_asset4_locale = str(self.trailer_asset4_locale.currentText()).split(":", 1)[0]

    def set_trailer_asset5_role(self):
        settings.trailer_asset5_role = str(self.trailer_asset5_role.currentText())

        if settings.trailer_asset5_role != "notes":
            self.trailer_asset5_locale.setEnabled(True)

        else:
            self.trailer_asset5_locale.setEnabled(False)

    def set_trailer_asset5_locale(self):
        settings.trailer_asset5_locale = str(self.trailer_asset5_locale.currentText()).split(":", 1)[0]

    def set_trailer_asset6_role(self):
        settings.trailer_asset6_role = str(self.trailer_asset6_role.currentText())

        if settings.trailer_asset6_role != "notes":
            self.trailer_asset6_locale.setEnabled(True)

        else:
            self.trailer_asset6_locale.setEnabled(False)

    def set_trailer_asset6_locale(self):
        settings.trailer_asset6_locale = str(self.trailer_asset6_locale.currentText()).split(":", 1)[0]

    def set_trailer_asset7_role(self):
        settings.trailer_asset7_role = str(self.trailer_asset7_role.currentText())

        if settings.trailer_asset7_role != "notes":
            self.trailer_asset7_locale.setEnabled(True)

        else:
            self.trailer_asset7_locale.setEnabled(False)

    def set_trailer_asset7_locale(self):
        settings.trailer_asset7_locale = str(self.trailer_asset7_locale.currentText()).split(":", 1)[0]

    def set_trailer_asset8_role(self):
        settings.trailer_asset8_role = str(self.trailer_asset8_role.currentText())

        if settings.trailer_asset8_role != "notes":
            self.trailer_asset8_locale.setEnabled(True)

        else:
            self.trailer_asset8_locale.setEnabled(False)

    def set_trailer_asset8_locale(self):
        settings.trailer_asset8_locale = str(self.trailer_asset8_locale.currentText()).split(":", 1)[0]

    # poster art
    def set_poster_locale(self):
        settings.poster_locale = str(self.comboPoster.currentText()).split(":", 1)[0]

    def poster_file_dlg(self):
        settings.poster_file_path = \
            str(QtGui.QFileDialog.getOpenFileName(
                parent=self,
                caption="Locate poster art file",
                directory=settings.directory,
                filter="Graphics files (*.jpg *.jpeg *.lsr)"))

        self.poster_file_lbl.setText(settings.poster_file_path)

        if settings.poster_file_path:
            settings.directory = os.path.dirname(settings.poster_file_path)

            if os.path.splitext(settings.poster_file_path)[1] == ".lsr":
                try:
                    up_level = os.path.dirname(os.path.dirname(settings.poster_file_path))
                    chapter_png = os.path.basename(os.path.splitext(settings.poster_file_path)[0]) + ".png"
                    path_to_png = up_level + "/" + chapter_png

                    poster_pixmap = QtGui.QPixmap(path_to_png)
                    poster_pixmap_meta_scaled = poster_pixmap.scaled(400, 400, QtCore.Qt.KeepAspectRatio)
                    poster_pixmap_scaled = poster_pixmap.scaled(600, 600, QtCore.Qt.KeepAspectRatio)
                    self.poster_pic_meta.setPixmap(poster_pixmap_meta_scaled)
                    self.poster_pic.setPixmap(poster_pixmap_scaled)

                except IOError:
                    return

            else:
                poster_pixmap = QtGui.QPixmap(settings.poster_file_path)
                poster_pixmap_meta_scaled = poster_pixmap.scaled(400, 400, QtCore.Qt.KeepAspectRatio)
                poster_pixmap_scaled = poster_pixmap.scaled(600, 600, QtCore.Qt.KeepAspectRatio)
                self.poster_pic_meta.setPixmap(poster_pixmap_meta_scaled)
                self.poster_pic.setPixmap(poster_pixmap_scaled)

    # product
    def set_product1_check(self):
        settings.product1_check = self.product1_check.isChecked()
        self.set_product1_terr()

        if not settings.product1_check:
            index_rating1_sys = self.rating1_sys.findText(
                ratings.systems[""], QtCore.Qt.MatchFixedString)
            self.rating1_sys.setCurrentIndex(index_rating1_sys)

            if (settings.product2_check and settings.product2_terr == "CA") \
                    or (settings.product3_check and settings.product3_terr == "CA") \
                    or (settings.product4_check and settings.product4_terr == "CA"):
                return

            else:
                index_rating5_sys = self.rating5_sys.findText(
                    ratings.systems[""], QtCore.Qt.MatchFixedString)
                self.rating5_sys.setCurrentIndex(index_rating5_sys)

    def set_product2_check(self):
        settings.product2_check = self.product2_check.isChecked()
        self.set_product2_terr()

        if not settings.product2_check:
            index_rating2_sys = self.rating2_sys.findText(
                ratings.systems[""], QtCore.Qt.MatchFixedString)
            self.rating2_sys.setCurrentIndex(index_rating2_sys)

            if (settings.product1_check and settings.product1_terr == "CA") \
                    or (settings.product3_check and settings.product3_terr == "CA") \
                    or (settings.product4_check and settings.product4_terr == "CA"):
                return

            else:
                index_rating5_sys = self.rating5_sys.findText(
                    ratings.systems[""], QtCore.Qt.MatchFixedString)
                self.rating5_sys.setCurrentIndex(index_rating5_sys)

    def set_product3_check(self):
        settings.product3_check = self.product3_check.isChecked()
        self.set_product3_terr()

        if not settings.product3_check:
            index_rating3_sys = self.rating3_sys.findText(
                ratings.systems[""], QtCore.Qt.MatchFixedString)
            self.rating3_sys.setCurrentIndex(index_rating3_sys)

            if (settings.product1_check and settings.product1_terr == "CA") \
                    or (settings.product2_check and settings.product2_terr == "CA") \
                    or (settings.product4_check and settings.product4_terr == "CA"):
                return

            else:
                index_rating5_sys = self.rating5_sys.findText(
                    ratings.systems[""], QtCore.Qt.MatchFixedString)
                self.rating5_sys.setCurrentIndex(index_rating5_sys)

    def set_product4_check(self):
        settings.product4_check = self.product4_check.isChecked()
        self.set_product4_terr()

        if not settings.product4_check:
            index_rating4_sys = self.rating4_sys.findText(
                ratings.systems[""], QtCore.Qt.MatchFixedString)
            self.rating4_sys.setCurrentIndex(index_rating4_sys)

            if (settings.product1_check and settings.product1_terr == "CA") \
                    or (settings.product2_check and settings.product2_terr == "CA") \
                    or (settings.product3_check and settings.product3_terr == "CA"):
                return

            else:
                index_rating5_sys = self.rating5_sys.findText(
                    ratings.systems[""], QtCore.Qt.MatchFixedString)
                self.rating5_sys.setCurrentIndex(index_rating5_sys)

    def set_product1_sales_start_check(self):
        settings.product1_sales_start_check = self.product1_sales_start_check.isChecked()

    def set_product2_sales_start_check(self):
        settings.product2_sales_start_check = self.product2_sales_start_check.isChecked()

    def set_product3_sales_start_check(self):
        settings.product3_sales_start_check = self.product3_sales_start_check.isChecked()

    def set_product4_sales_start_check(self):
        settings.product4_sales_start_check = self.product4_sales_start_check.isChecked()

    def set_product1_sales_end_check(self):
        settings.product1_sales_end_check = self.product1_sales_end_check.isChecked()

    def set_product2_sales_end_check(self):
        settings.product2_sales_end_check = self.product2_sales_end_check.isChecked()

    def set_product3_sales_end_check(self):
        settings.product3_sales_end_check = self.product3_sales_end_check.isChecked()

    def set_product4_sales_end_check(self):
        settings.product4_sales_end_check = self.product4_sales_end_check.isChecked()
    
    def set_product1_preorder_check(self):
        settings.product1_preorder_check = self.product1_preorder_check.isChecked()

    def set_product2_preorder_check(self):
        settings.product2_preorder_check = self.product2_preorder_check.isChecked()

    def set_product3_preorder_check(self):
        settings.product3_preorder_check = self.product3_preorder_check.isChecked()

    def set_product4_preorder_check(self):
        settings.product4_preorder_check = self.product4_preorder_check.isChecked()
    
    def set_product1_vod_start_check(self):
        settings.product1_vod_start_check = self.product1_vod_start_check.isChecked()

    def set_product2_vod_start_check(self):
        settings.product2_vod_start_check = self.product2_vod_start_check.isChecked()

    def set_product3_vod_start_check(self):
        settings.product3_vod_start_check = self.product3_vod_start_check.isChecked()

    def set_product4_vod_start_check(self):
        settings.product4_vod_start_check = self.product4_vod_start_check.isChecked()
    
    def set_product1_vod_end_check(self):
        settings.product1_vod_end_check = self.product1_vod_end_check.isChecked()

    def set_product2_vod_end_check(self):
        settings.product2_vod_end_check = self.product2_vod_end_check.isChecked()

    def set_product3_vod_end_check(self):
        settings.product3_vod_end_check = self.product3_vod_end_check.isChecked()

    def set_product4_vod_end_check(self):
        settings.product4_vod_end_check = self.product4_vod_end_check.isChecked()
    
    def set_product1_physical_check(self):
        settings.product1_physical_check = self.product1_physical_check.isChecked()

    def set_product2_physical_check(self):
        settings.product2_physical_check = self.product2_physical_check.isChecked()

    def set_product3_physical_check(self):
        settings.product3_physical_check = self.product3_physical_check.isChecked()

    def set_product4_physical_check(self):
        settings.product4_physical_check = self.product4_physical_check.isChecked()

    def set_product1_price_sd_check(self):
        settings.product1_price_sd_check = self.product1_price_sd_check.isChecked()

    def set_product2_price_sd_check(self):
        settings.product2_price_sd_check = self.product2_price_sd_check.isChecked()

    def set_product3_price_sd_check(self):
        settings.product3_price_sd_check = self.product3_price_sd_check.isChecked()

    def set_product4_price_sd_check(self):
        settings.product4_price_sd_check = self.product4_price_sd_check.isChecked()

    def set_product1_price_hd_check(self):
        settings.product1_price_hd_check = self.product1_price_hd_check.isChecked()

    def set_product2_price_hd_check(self):
        settings.product2_price_hd_check = self.product2_price_hd_check.isChecked()

    def set_product3_price_hd_check(self):
        settings.product3_price_hd_check = self.product3_price_hd_check.isChecked()

    def set_product4_price_hd_check(self):
        settings.product4_price_hd_check = self.product4_price_hd_check.isChecked()

    def set_product1_vod_type_check(self):
        settings.product1_vod_type_check = self.product1_vod_type_check.isChecked()

    def set_product2_vod_type_check(self):
        settings.product2_vod_type_check = self.product2_vod_type_check.isChecked()

    def set_product3_vod_type_check(self):
        settings.product3_vod_type_check = self.product3_vod_type_check.isChecked()

    def set_product4_vod_type_check(self):
        settings.product4_vod_type_check = self.product4_vod_type_check.isChecked()

    def set_product1_terr(self):
        settings.product1_terr = str(self.product1_terr.currentText())

        if settings.product1_check:
            if settings.product1_terr in ratings.systems:
                index_rating1_sys = self.rating1_sys.findText(
                    ratings.systems[settings.product1_terr], QtCore.Qt.MatchFixedString)
                self.rating1_sys.setCurrentIndex(index_rating1_sys)

                if settings.product1_terr == "CA":
                    index_rating1_sys_qc = self.rating5_sys.findText(
                        ratings.systems["QC"], QtCore.Qt.MatchFixedString)
                    self.rating5_sys.setCurrentIndex(index_rating1_sys_qc)

                else:
                    if (settings.product2_check and settings.product2_terr == "CA") \
                            or (settings.product3_check and settings.product3_terr == "CA") \
                            or (settings.product4_check and settings.product4_terr == "CA"):
                        return

                    else:
                        index_rating5_sys = self.rating5_sys.findText(
                            ratings.systems[""], QtCore.Qt.MatchFixedString)
                        self.rating5_sys.setCurrentIndex(index_rating5_sys)

        else:
            if (settings.product2_check and settings.product2_terr == "CA") \
                    or (settings.product3_check and settings.product3_terr == "CA") \
                    or (settings.product4_check and settings.product4_terr == "CA"):
                return

            else:
                index_rating1_sys = self.rating1_sys.findText(
                    ratings.systems[""], QtCore.Qt.MatchFixedString)
                self.rating1_sys.setCurrentIndex(index_rating1_sys)

    def set_product1_sale_clear(self):
        settings.product1_sale_clear = str(self.product1_sale_clear.currentText())

    def set_product1_price_sd(self):
        settings.product1_price_sd = " ".join(unicode(self.product1_price_sd.text()).split())

        self.product2_price_sd.setText(settings.product1_price_sd)
        self.product3_price_sd.setText(settings.product1_price_sd)
        self.product4_price_sd.setText(settings.product1_price_sd)

    def set_product1_price_hd(self):
        settings.product1_price_hd = " ".join(unicode(self.product1_price_hd.text()).split())

        self.product2_price_hd.setText(settings.product1_price_hd)
        self.product3_price_hd.setText(settings.product1_price_hd)
        self.product4_price_hd.setText(settings.product1_price_hd)
    
    def set_product1_sales_start(self):
        settings.product1_sales_start = " ".join(unicode(self.product1_sales_start.text()).split())

        self.product2_sales_start.setText(settings.product1_sales_start)
        self.product3_sales_start.setText(settings.product1_sales_start)
        self.product4_sales_start.setText(settings.product1_sales_start)

        self.product1_vod_start.setText(settings.product1_sales_start)
        self.product2_vod_start.setText(settings.product1_sales_start)
        self.product3_vod_start.setText(settings.product1_sales_start)
        self.product4_vod_start.setText(settings.product1_sales_start)

        self.product1_physical.setText(settings.product1_sales_start)
        self.product2_physical.setText(settings.product1_sales_start)
        self.product3_physical.setText(settings.product1_sales_start)
        self.product4_physical.setText(settings.product1_sales_start)
    
    def set_product1_sales_end(self):
        settings.product1_sales_end = " ".join(unicode(self.product1_sales_end.text()).split())

        self.product2_sales_end.setText(settings.product1_sales_end)
        self.product3_sales_end.setText(settings.product1_sales_end)
        self.product4_sales_end.setText(settings.product1_sales_end)

        self.product1_vod_end.setText(settings.product1_sales_end)
        self.product2_vod_end.setText(settings.product1_sales_end)
        self.product3_vod_end.setText(settings.product1_sales_end)
        self.product4_vod_end.setText(settings.product1_sales_end)
    
    def set_product1_preorder(self):
        settings.product1_preorder = " ".join(unicode(self.product1_preorder.text()).split())

        self.product2_preorder.setText(settings.product1_preorder)
        self.product3_preorder.setText(settings.product1_preorder)
        self.product4_preorder.setText(settings.product1_preorder)
    
    def set_product1_vod_clear(self):
        settings.product1_vod_clear = str(self.product1_vod_clear.currentText())
    
    def set_product1_vod_type(self):
        settings.product1_vod_type = str(self.product1_vod_type.currentText())
    
    def set_product1_vod_start(self):
        settings.product1_vod_start = " ".join(unicode(self.product1_vod_start.text()).split())

        self.product2_vod_start.setText(settings.product1_vod_start)
        self.product3_vod_start.setText(settings.product1_vod_start)
        self.product4_vod_start.setText(settings.product1_vod_start)
    
    def set_product1_vod_end(self):
        settings.product1_vod_end = " ".join(unicode(self.product1_vod_end.text()).split())

        self.product2_vod_end.setText(settings.product1_vod_end)
        self.product3_vod_end.setText(settings.product1_vod_end)
        self.product4_vod_end.setText(settings.product1_vod_end)
    
    def set_product1_physical(self):
        settings.product1_physical = " ".join(unicode(self.product1_physical.text()).split())

        self.product2_physical.setText(settings.product1_physical)
        self.product3_physical.setText(settings.product1_physical)
        self.product4_physical.setText(settings.product1_physical)
    
    def set_product2_terr(self):
        settings.product2_terr = str(self.product2_terr.currentText())

        if settings.product2_check:
            if settings.product2_terr in ratings.systems:
                index_rating2_sys = self.rating2_sys.findText(
                    ratings.systems[settings.product2_terr], QtCore.Qt.MatchFixedString)
                self.rating2_sys.setCurrentIndex(index_rating2_sys)

                if settings.product2_terr == "CA":
                    index_rating2_sys_qc = self.rating5_sys.findText(
                        ratings.systems["QC"], QtCore.Qt.MatchFixedString)
                    self.rating5_sys.setCurrentIndex(index_rating2_sys_qc)

                else:
                    if (settings.product1_check and settings.product1_terr == "CA")\
                            or (settings.product3_check and settings.product3_terr == "CA")\
                            or (settings.product4_check and settings.product4_terr == "CA"):
                        return

                    else:
                        index_rating5_sys = self.rating5_sys.findText(
                            ratings.systems[""], QtCore.Qt.MatchFixedString)
                        self.rating5_sys.setCurrentIndex(index_rating5_sys)

        else:
            if (settings.product1_check and settings.product1_terr == "CA") \
                    or (settings.product3_check and settings.product3_terr == "CA") \
                    or (settings.product4_check and settings.product4_terr == "CA"):
                return

            else:
                index_rating2_sys = self.rating2_sys.findText(
                    ratings.systems[""], QtCore.Qt.MatchFixedString)
                self.rating2_sys.setCurrentIndex(index_rating2_sys)

    def set_product2_sale_clear(self):
        settings.product2_sale_clear = str(self.product2_sale_clear.currentText())

    def set_product2_price_sd(self):
        settings.product2_price_sd = " ".join(unicode(self.product2_price_sd.text()).split())

    def set_product2_price_hd(self):
        settings.product2_price_hd = " ".join(unicode(self.product2_price_hd.text()).split())
    
    def set_product2_sales_start(self):
        settings.product2_sales_start = " ".join(unicode(self.product2_sales_start.text()).split())
    
    def set_product2_sales_end(self):
        settings.product2_sales_end = " ".join(unicode(self.product2_sales_end.text()).split())
    
    def set_product2_preorder(self):
        settings.product2_preorder = " ".join(unicode(self.product2_preorder.text()).split())
    
    def set_product2_vod_clear(self):
        settings.product2_vod_clear = str(self.product2_vod_clear.currentText())
    
    def set_product2_vod_type(self):
        settings.product2_vod_type = str(self.product2_vod_type.currentText())
    
    def set_product2_vod_start(self):
        settings.product2_vod_start = " ".join(unicode(self.product2_vod_start.text()).split())
    
    def set_product2_vod_end(self):
        settings.product2_vod_end = " ".join(unicode(self.product2_vod_end.text()).split())
    
    def set_product2_physical(self):
        settings.product2_physical = " ".join(unicode(self.product2_physical.text()).split())
    
    def set_product3_terr(self):
        settings.product3_terr = str(self.product3_terr.currentText())

        if settings.product3_check:
            if settings.product3_terr in ratings.systems:
                index_rating3_sys = self.rating3_sys.findText(
                    ratings.systems[settings.product3_terr], QtCore.Qt.MatchFixedString)
                self.rating3_sys.setCurrentIndex(index_rating3_sys)

                if settings.product3_terr == "CA":
                    index_rating3_sys_qc = self.rating5_sys.findText(
                        ratings.systems["QC"], QtCore.Qt.MatchFixedString)
                    self.rating5_sys.setCurrentIndex(index_rating3_sys_qc)

                else:
                    if (settings.product1_check and settings.product1_terr == "CA")\
                            or (settings.product2_check and settings.product2_terr == "CA")\
                            or (settings.product4_check and settings.product4_terr == "CA"):
                        return

                    else:
                        index_rating5_sys = self.rating5_sys.findText(
                            ratings.systems[""], QtCore.Qt.MatchFixedString)
                        self.rating5_sys.setCurrentIndex(index_rating5_sys)

        else:
            if (settings.product1_check and settings.product1_terr == "CA") \
                    or (settings.product2_check and settings.product2_terr == "CA") \
                    or (settings.product4_check and settings.product4_terr == "CA"):
                return

            else:
                index_rating3_sys = self.rating3_sys.findText(
                    ratings.systems[""], QtCore.Qt.MatchFixedString)
                self.rating3_sys.setCurrentIndex(index_rating3_sys)

    def set_product3_sale_clear(self):
        settings.product3_sale_clear = str(self.product3_sale_clear.currentText())

    def set_product3_price_sd(self):
        settings.product3_price_sd = " ".join(unicode(self.product3_price_sd.text()).split())

    def set_product3_price_hd(self):
        settings.product3_price_hd = " ".join(unicode(self.product3_price_hd.text()).split())
    
    def set_product3_sales_start(self):
        settings.product3_sales_start = " ".join(unicode(self.product3_sales_start.text()).split())
    
    def set_product3_sales_end(self):
        settings.product3_sales_end = " ".join(unicode(self.product3_sales_end.text()).split())
    
    def set_product3_preorder(self):
        settings.product3_preorder = " ".join(unicode(self.product3_preorder.text()).split())
    
    def set_product3_vod_clear(self):
        settings.product3_vod_clear = str(self.product3_vod_clear.currentText())
    
    def set_product3_vod_type(self):
        settings.product3_vod_type = str(self.product3_vod_type.currentText())
    
    def set_product3_vod_start(self):
        settings.product3_vod_start = " ".join(unicode(self.product3_vod_start.text()).split())
    
    def set_product3_vod_end(self):
        settings.product3_vod_end = " ".join(unicode(self.product3_vod_end.text()).split())
    
    def set_product3_physical(self):
        settings.product3_physical = " ".join(unicode(self.product3_physical.text()).split())
    
    def set_product4_terr(self):
        settings.product4_terr = str(self.product4_terr.currentText())

        if settings.product4_check:
            if settings.product4_terr in ratings.systems:
                index_rating4_sys = self.rating4_sys.findText(
                    ratings.systems[settings.product4_terr], QtCore.Qt.MatchFixedString)
                self.rating4_sys.setCurrentIndex(index_rating4_sys)

                if settings.product4_terr == "CA":
                    index_rating4_sys_qc = self.rating5_sys.findText(
                        ratings.systems["QC"], QtCore.Qt.MatchFixedString)
                    self.rating5_sys.setCurrentIndex(index_rating4_sys_qc)

                else:
                    if (settings.product1_check and settings.product1_terr == "CA")\
                            or (settings.product2_check and settings.product2_terr == "CA")\
                            or (settings.product3_check and settings.product3_terr == "CA"):
                        return

                    else:
                        index_rating5_sys = self.rating5_sys.findText(
                            ratings.systems[""], QtCore.Qt.MatchFixedString)
                        self.rating5_sys.setCurrentIndex(index_rating5_sys)

        else:
            if (settings.product1_check and settings.product1_terr == "CA") \
                    or (settings.product2_check and settings.product2_terr == "CA") \
                    or (settings.product3_check and settings.product3_terr == "CA"):
                return

            else:
                index_rating4_sys = self.rating4_sys.findText(
                    ratings.systems[""], QtCore.Qt.MatchFixedString)
                self.rating4_sys.setCurrentIndex(index_rating4_sys)

    def set_product4_sale_clear(self):
        settings.product4_sale_clear = str(self.product4_sale_clear.currentText())

    def set_product4_price_sd(self):
        settings.product4_price_sd = " ".join(unicode(self.product4_price_sd.text()).split())

    def set_product4_price_hd(self):
        settings.product4_price_hd = " ".join(unicode(self.product4_price_hd.text()).split())
    
    def set_product4_sales_start(self):
        settings.product4_sales_start = " ".join(unicode(self.product4_sales_start.text()).split())
    
    def set_product4_sales_end(self):
        settings.product4_sales_end = " ".join(unicode(self.product4_sales_end.text()).split())
    
    def set_product4_preorder(self):
        settings.product4_preorder = " ".join(unicode(self.product4_preorder.text()).split())
    
    def set_product4_vod_clear(self):
        settings.product4_vod_clear = str(self.product4_vod_clear.currentText())
    
    def set_product4_vod_type(self):
        settings.product4_vod_type = str(self.product4_vod_type.currentText())
    
    def set_product4_vod_start(self):
        settings.product4_vod_start = " ".join(unicode(self.product4_vod_start.text()).split())
    
    def set_product4_vod_end(self):
        settings.product4_vod_end = " ".join(unicode(self.product4_vod_end.text()).split())
    
    def set_product4_physical(self):
        settings.product4_physical = " ".join(unicode(self.product4_physical.text()).split())
    
    # localization
    def set_localized_check_1(self):
        settings.localized_check_1 = self.localized_check_1.isChecked()

    def set_localized_locale_1(self):
        settings.localized_locale_1 = str(self.localized_locale_1.currentText()).split(":", 1)[0]

    def set_localized_title_1(self):
        settings.localized_title_1 = " ".join(unicode(self.localized_title_1.text()).split())

    def set_localized_synopsis_1(self):
        settings.localized_synopsis_1 = " ".join(unicode(self.localized_synopsis_1.toPlainText()).split())

    def set_localized_check_2(self):
        settings.localized_check_2 = self.localized_check_2.isChecked()

    def set_localized_locale_2(self):
        settings.localized_locale_2 = str(self.localized_locale_2.currentText()).split(":", 2)[0]

    def set_localized_title_2(self):
        settings.localized_title_2 = " ".join(unicode(self.localized_title_2.text()).split())

    def set_localized_synopsis_2(self):
        settings.localized_synopsis_2 = " ".join(unicode(self.localized_synopsis_2.toPlainText()).split())

    def set_localized_check_3(self):
        settings.localized_check_3 = self.localized_check_3.isChecked()

    def set_localized_locale_3(self):
        settings.localized_locale_3 = str(self.localized_locale_3.currentText()).split(":", 3)[0]

    def set_localized_title_3(self):
        settings.localized_title_3 = " ".join(unicode(self.localized_title_3.text()).split())

    def set_localized_synopsis_3(self):
        settings.localized_synopsis_3 = " ".join(unicode(self.localized_synopsis_3.toPlainText()).split())

    def set_localized_check_4(self):
        settings.localized_check_4 = self.localized_check_4.isChecked()

    def set_localized_locale_4(self):
        settings.localized_locale_4 = str(self.localized_locale_4.currentText()).split(":", 4)[0]

    def set_localized_title_4(self):
        settings.localized_title_4 = " ".join(unicode(self.localized_title_4.text()).split())

    def set_localized_synopsis_4(self):
        settings.localized_synopsis_4 = " ".join(unicode(self.localized_synopsis_4.toPlainText()).split())

    # localized trailer
    def loc_trailer_file_dlg(self):
        settings.loc_trailer_file_path = \
            str(QtGui.QFileDialog.getOpenFileName(
                parent=self,
                caption="Locate trailer file",
                directory=settings.directory,
                filter="Quicktime files (*.mov)"))

        self.loc_trailer_file_lbl.setText(settings.loc_trailer_file_path)

        if settings.loc_trailer_file_path:
            settings.directory = os.path.dirname(settings.loc_trailer_file_path)

    def loc_trailer_md5_start(self):
        if settings.loc_trailer_file_path == "":
            path_msg = QtGui.QMessageBox()

            path_msg.setIcon(QtGui.QMessageBox.Information)
            path_msg.setText("Please select a localized trailer file.")
            path_msg.setWindowTitle("Input needed")
            path_msg.setStandardButtons(QtGui.QMessageBox.Ok)
            path_msg.exec_()
            return

        else:
            self.loc_trailer_md5_stop_btn.setEnabled(True)
            self.loc_trailer_md5_start_btn.setEnabled(False)
            self.loc_trailer_md5_progress.setRange(0, 0)
            self.tabWidget.tabBar().setTabTextColor(13, QtCore.Qt.red)
            self.connect(self.loc_trailer_md5_thread, QtCore.SIGNAL("finished()"), self.loc_trailer_md5_done)
            self.loc_trailer_md5_thread.start()

    def loc_trailer_md5_stop(self):
        self.loc_trailer_md5_thread.terminate()
        self.loc_trailer_md5_stop_btn.setEnabled(False)
        self.loc_trailer_md5_start_btn.setEnabled(True)
        self.tabWidget.tabBar().setTabTextColor(13, QtCore.Qt.black)
        self.loc_trailer_md5_progress.setRange(0, 1)
        self.loc_trailer_md5_progress.setValue(0)

    def loc_trailer_md5_done(self):
        self.loc_trailer_md5_stop_btn.setEnabled(False)
        self.loc_trailer_md5_start_btn.setEnabled(True)
        self.loc_trailer_md5_lbl.setText(settings.loc_trailer_md5)
        self.tabWidget.tabBar().setTabTextColor(13, QtCore.Qt.black)
        self.loc_trailer_md5_progress.setRange(0, 1)
        self.loc_trailer_md5_progress.setValue(1)

    def set_loc_trailer_md5_lbl(self):
        loc_trailer_md5_clean = " ".join(unicode(self.loc_trailer_md5_lbl.text()).split())
        settings.loc_trailer_md5 = loc_trailer_md5_clean

    def set_loc_trailer_still_tc(self):
        settings.loc_trailer_still = " ".join(unicode(self.loc_trailer_still_tc.text()).split())

    def set_loc_trailer_tc_format(self):
        settings.loc_trailer_tc = str(self.tc_format_loc_trailer.currentText())

    def set_loc_trailer_audio(self):
        settings.loc_trailer_audio = str(self.loc_comboTrailerAudio.currentText()).split(":", 1)[0]

    def set_loc_trailer_top_crop(self):
        settings.loc_trailer_crop_top = " ".join(unicode(self.loc_trailer_top_crop.text()).split())

    def set_loc_trailer_bottom_crop(self):
        settings.loc_trailer_crop_bottom = " ".join(unicode(self.loc_trailer_bottom_crop.text()).split())

    def set_loc_trailer_left_crop(self):
        settings.loc_trailer_crop_left = " ".join(unicode(self.loc_trailer_left_crop.text()).split())

    def set_loc_trailer_right_crop(self):
        settings.loc_trailer_crop_right = " ".join(unicode(self.loc_trailer_right_crop.text()).split())

    def check_loc_trailer_narr(self):
        settings.loc_trailer_check_narr = self.loc_trailer_narr.isChecked()
        self.loc_comboNarrTrailer.setEnabled(self.loc_trailer_narr.isChecked())

    def set_narr_loc_trailer(self):
        settings.loc_narr_trailer = str(self.loc_comboNarrTrailer.currentText()).split(":", 1)[0]

    def check_loc_trailer_subs(self):
        settings.loc_trailer_check_subs = self.loc_trailer_subs.isChecked()
        self.loc_comboSubTrailer.setEnabled(self.loc_trailer_subs.isChecked())

    def set_sub_loc_trailer(self):
        settings.loc_sub_trailer = str(self.loc_comboSubTrailer.currentText()).split(":", 1)[0]

    def add_territory(self):

        box = QtGui.QComboBox(self)
        box.addItems(self.country_values)
        box.setObjectName("territory%d" % self.loc_trailer_count)
        box.currentIndexChanged.connect(self.set_loc_trailer_terr)
        # index_loc_trailer_terr = box.findText("US", QtCore.Qt.MatchFixedString)
        box.setCurrentIndex(1)
        box.setCurrentIndex(0)

        self.loc_trailer_terr_lyt.addWidget(box, 0, self.loc_trailer_count)

        self.loc_trailer_count = len(settings.loc_trailer_territories.keys())

    def del_territory(self):
        if self.loc_trailer_terr_lyt.count() > 1:
            to_delete = self.loc_trailer_terr_lyt.takeAt(self.loc_trailer_terr_lyt.count() - 1)

            widget = to_delete.widget()
            if widget:
                widget.deleteLater()

        if len(settings.loc_trailer_territories.keys()) > 1:
            settings.loc_trailer_territories.pop(settings.loc_trailer_territories.keys()[-1])

        self.loc_trailer_count = len(settings.loc_trailer_territories.keys())

    def set_loc_trailer_terr(self):
        sender = self.sender()

        settings.loc_trailer_territories.update({str(sender.objectName()): str(sender.currentText())})

    # localized trailer assets
    def loc_trailer_asset1_dlg(self):
        settings.loc_trailer_asset1_path = \
            str(QtGui.QFileDialog.getOpenFileName(
                parent=self,
                caption="Locate asset file",
                directory=settings.directory))

        self.loc_trailer_asset1_lbl.setText(os.path.basename(settings.loc_trailer_asset1_path))

        if settings.loc_trailer_asset1_path:
            settings.directory = os.path.dirname(settings.loc_trailer_asset1_path)

    def loc_trailer_asset2_dlg(self):
        settings.loc_trailer_asset2_path = \
            str(QtGui.QFileDialog.getOpenFileName(
                parent=self,
                caption="Locate asset file",
                directory=settings.directory))

        self.loc_trailer_asset2_lbl.setText(os.path.basename(settings.loc_trailer_asset2_path))

        if settings.loc_trailer_asset2_path:
            settings.directory = os.path.dirname(settings.loc_trailer_asset2_path)

    def loc_trailer_asset3_dlg(self):
        settings.loc_trailer_asset3_path = \
            str(QtGui.QFileDialog.getOpenFileName(
                parent=self,
                caption="Locate asset file",
                directory=settings.directory))

        self.loc_trailer_asset3_lbl.setText(os.path.basename(settings.loc_trailer_asset3_path))

        if settings.loc_trailer_asset3_path:
            settings.directory = os.path.dirname(settings.loc_trailer_asset3_path)

    def loc_trailer_asset4_dlg(self):
        settings.loc_trailer_asset4_path = \
            str(QtGui.QFileDialog.getOpenFileName(
                parent=self,
                caption="Locate asset file",
                directory=settings.directory))

        self.loc_trailer_asset4_lbl.setText(os.path.basename(settings.loc_trailer_asset4_path))

        if settings.loc_trailer_asset4_path:
            settings.directory = os.path.dirname(settings.loc_trailer_asset4_path)

    def loc_trailer_asset5_dlg(self):
        settings.loc_trailer_asset5_path = \
            str(QtGui.QFileDialog.getOpenFileName(
                parent=self,
                caption="Locate asset file",
                directory=settings.directory))

        self.loc_trailer_asset5_lbl.setText(os.path.basename(settings.loc_trailer_asset5_path))

        if settings.loc_trailer_asset5_path:
            settings.directory = os.path.dirname(settings.loc_trailer_asset5_path)

    def loc_trailer_asset6_dlg(self):
        settings.loc_trailer_asset6_path = \
            str(QtGui.QFileDialog.getOpenFileName(
                parent=self,
                caption="Locate asset file",
                directory=settings.directory))

        self.loc_trailer_asset6_lbl.setText(os.path.basename(settings.loc_trailer_asset6_path))

        if settings.loc_trailer_asset6_path:
            settings.directory = os.path.dirname(settings.loc_trailer_asset6_path)

    def loc_trailer_asset7_dlg(self):
        settings.loc_trailer_asset7_path = \
            str(QtGui.QFileDialog.getOpenFileName(
                parent=self,
                caption="Locate asset file",
                directory=settings.directory))

        self.loc_trailer_asset7_lbl.setText(os.path.basename(settings.loc_trailer_asset7_path))

        if settings.loc_trailer_asset7_path:
            settings.directory = os.path.dirname(settings.loc_trailer_asset7_path)

    def loc_trailer_asset8_dlg(self):
        settings.loc_trailer_asset8_path = \
            str(QtGui.QFileDialog.getOpenFileName(
                parent=self,
                caption="Locate asset file",
                directory=settings.directory))

        self.loc_trailer_asset8_lbl.setText(os.path.basename(settings.loc_trailer_asset8_path))

        if settings.loc_trailer_asset8_path:
            settings.directory = os.path.dirname(settings.loc_trailer_asset8_path)

    def set_loc_trailer_asset1_role(self):
        settings.loc_trailer_asset1_role = str(self.loc_trailer_asset1_role.currentText())

        if settings.loc_trailer_asset1_role != "notes":
            self.loc_trailer_asset1_locale.setEnabled(True)

        else:
            self.loc_trailer_asset1_locale.setEnabled(False)

    def set_loc_trailer_asset1_locale(self):
        settings.loc_trailer_asset1_locale = str(self.loc_trailer_asset1_locale.currentText()).split(":", 1)[0]

    def set_loc_trailer_asset2_role(self):
        settings.loc_trailer_asset2_role = str(self.loc_trailer_asset2_role.currentText())

        if settings.loc_trailer_asset2_role != "notes":
            self.loc_trailer_asset2_locale.setEnabled(True)

        else:
            self.loc_trailer_asset2_locale.setEnabled(False)

    def set_loc_trailer_asset2_locale(self):
        settings.loc_trailer_asset2_locale = str(self.loc_trailer_asset2_locale.currentText()).split(":", 1)[0]

    def set_loc_trailer_asset3_role(self):
        settings.loc_trailer_asset3_role = str(self.loc_trailer_asset3_role.currentText())

        if settings.loc_trailer_asset3_role != "notes":
            self.loc_trailer_asset3_locale.setEnabled(True)

        else:
            self.loc_trailer_asset3_locale.setEnabled(False)

    def set_loc_trailer_asset3_locale(self):
        settings.loc_trailer_asset3_locale = str(self.loc_trailer_asset3_locale.currentText()).split(":", 1)[0]

    def set_loc_trailer_asset4_role(self):
        settings.loc_trailer_asset4_role = str(self.loc_trailer_asset4_role.currentText())

        if settings.loc_trailer_asset4_role != "notes":
            self.loc_trailer_asset4_locale.setEnabled(True)

        else:
            self.loc_trailer_asset4_locale.setEnabled(False)

    def set_loc_trailer_asset4_locale(self):
        settings.loc_trailer_asset4_locale = str(self.loc_trailer_asset4_locale.currentText()).split(":", 1)[0]

    def set_loc_trailer_asset5_role(self):
        settings.loc_trailer_asset5_role = str(self.loc_trailer_asset5_role.currentText())

        if settings.loc_trailer_asset5_role != "notes":
            self.loc_trailer_asset5_locale.setEnabled(True)

        else:
            self.loc_trailer_asset5_locale.setEnabled(False)

    def set_loc_trailer_asset5_locale(self):
        settings.loc_trailer_asset5_locale = str(self.loc_trailer_asset5_locale.currentText()).split(":", 1)[0]

    def set_loc_trailer_asset6_role(self):
        settings.loc_trailer_asset6_role = str(self.loc_trailer_asset6_role.currentText())

        if settings.loc_trailer_asset6_role != "notes":
            self.loc_trailer_asset6_locale.setEnabled(True)

        else:
            self.loc_trailer_asset6_locale.setEnabled(False)

    def set_loc_trailer_asset6_locale(self):
        settings.loc_trailer_asset6_locale = str(self.loc_trailer_asset6_locale.currentText()).split(":", 1)[0]

    def set_loc_trailer_asset7_role(self):
        settings.loc_trailer_asset7_role = str(self.loc_trailer_asset7_role.currentText())

        if settings.loc_trailer_asset7_role != "notes":
            self.loc_trailer_asset7_locale.setEnabled(True)

        else:
            self.loc_trailer_asset7_locale.setEnabled(False)

    def set_loc_trailer_asset7_locale(self):
        settings.loc_trailer_asset7_locale = str(self.loc_trailer_asset7_locale.currentText()).split(":", 1)[0]

    def set_loc_trailer_asset8_role(self):
        settings.loc_trailer_asset8_role = str(self.loc_trailer_asset8_role.currentText())

        if settings.loc_trailer_asset8_role != "notes":
            self.loc_trailer_asset8_locale.setEnabled(True)

        else:
            self.loc_trailer_asset8_locale.setEnabled(False)

    def set_loc_trailer_asset8_locale(self):
        settings.loc_trailer_asset8_locale = str(self.loc_trailer_asset8_locale.currentText()).split(":", 1)[0]

    # process
    def set_provider(self):
        settings.provider = str(self.comboProvider.currentText()).split(":", 1)[-1].lstrip()

    def set_meta_locale(self):
        global_locale = self.comboMetaLanguage.currentText()

        global_index = self.comboOriginalLanguage.findText(global_locale, QtCore.Qt.MatchFixedString)
        self.comboOriginalLanguage.setCurrentIndex(global_index)
        self.comboFeatureAudio.setCurrentIndex(global_index)
        self.comboNarrFeature.setCurrentIndex(global_index)
        self.comboSubFeature.setCurrentIndex(global_index)
        self.chapter_locale_cb_main.setCurrentIndex(global_index)
        self.comboTrailerAudio.setCurrentIndex(global_index)
        self.comboNarrTrailer.setCurrentIndex(global_index)
        self.comboSubTrailer.setCurrentIndex(global_index)
        self.feat_asset1_locale.setCurrentIndex(global_index)
        self.feat_asset2_locale.setCurrentIndex(global_index)
        self.feat_asset3_locale.setCurrentIndex(global_index)
        self.feat_asset4_locale.setCurrentIndex(global_index)
        self.feat_asset5_locale.setCurrentIndex(global_index)
        self.feat_asset6_locale.setCurrentIndex(global_index)
        self.feat_asset7_locale.setCurrentIndex(global_index)
        self.feat_asset8_locale.setCurrentIndex(global_index)
        self.trailer_asset1_locale.setCurrentIndex(global_index)
        self.trailer_asset2_locale.setCurrentIndex(global_index)
        self.trailer_asset3_locale.setCurrentIndex(global_index)
        self.trailer_asset4_locale.setCurrentIndex(global_index)
        self.trailer_asset5_locale.setCurrentIndex(global_index)
        self.trailer_asset6_locale.setCurrentIndex(global_index)
        self.trailer_asset7_locale.setCurrentIndex(global_index)
        self.trailer_asset8_locale.setCurrentIndex(global_index)
        self.loc_comboTrailerAudio.setCurrentIndex(global_index)
        self.loc_comboNarrTrailer.setCurrentIndex(global_index)
        self.loc_comboSubTrailer.setCurrentIndex(global_index)
        self.loc_trailer_asset1_locale.setCurrentIndex(global_index)
        self.loc_trailer_asset2_locale.setCurrentIndex(global_index)
        self.loc_trailer_asset3_locale.setCurrentIndex(global_index)
        self.loc_trailer_asset4_locale.setCurrentIndex(global_index)
        self.loc_trailer_asset5_locale.setCurrentIndex(global_index)
        self.loc_trailer_asset6_locale.setCurrentIndex(global_index)
        self.loc_trailer_asset7_locale.setCurrentIndex(global_index)
        self.loc_trailer_asset8_locale.setCurrentIndex(global_index)
        self.comboPoster.setCurrentIndex(global_index)

        settings.language_meta = str(global_locale).split(":", 1)[0]

    def set_vendor(self):
        settings.vendor = " ".join(unicode(self.vendor_id.text()).split())

    def pack_info_path_dlg(self):
        settings.pack_info_path = \
            str(QtGui.QFileDialog.getOpenFileName(
                parent=self,
                caption="Locate package_info.txt",
                directory=settings.directory,
                filter="Text files (*.txt)"))

        self.pack_info_path_lbl.setText(settings.pack_info_path)

        if settings.pack_info_path:
            settings.directory = os.path.dirname(settings.pack_info_path)

            try:
                os.chdir(os.path.dirname(settings.pack_info_path))
                with codecs.open("package_info.txt", "r", encoding="utf8") as pack_info_text:
                    pack_info_lst = pack_info_text.readlines()

                    for i in pack_info_lst:
                        if i.startswith("Feature spoken audio"):
                            feat_burnt_subs = pack_info_lst[
                                                  pack_info_lst.index(i) + 2].split(
                                ":", 1)[-1].lstrip().rstrip() + ":"
                            index_feature_subs = self.comboSubFeature.findText(feat_burnt_subs,
                                                                                  QtCore.Qt.MatchStartsWith)
                            if index_feature_subs >= 0:
                                self.feat_subs.setChecked(True)
                                self.comboSubFeature.setCurrentIndex(index_feature_subs)

                            feat_burnt_narr = pack_info_lst[
                                                  pack_info_lst.index(i) + 3].split(
                                ":", 1)[-1].lstrip().rstrip() + ":"
                            index_feature_narr = self.comboNarrFeature.findText(feat_burnt_narr,
                                                                               QtCore.Qt.MatchStartsWith)
                            if index_feature_narr >= 0:
                                self.feat_narratives.setChecked(True)
                                self.comboNarrFeature.setCurrentIndex(index_feature_narr)

                        if i.startswith("Trailer spoken audio"):
                            trailer_burnt_subs = pack_info_lst[
                                                  pack_info_lst.index(i) + 2].split(
                                ":", 1)[-1].lstrip().rstrip() + ":"
                            index_trailer_subs = self.comboSubTrailer.findText(trailer_burnt_subs,
                                                                               QtCore.Qt.MatchStartsWith)
                            if index_trailer_subs >= 0:
                                self.trailer_subs.setChecked(True)
                                self.comboSubTrailer.setCurrentIndex(index_trailer_subs)

                            trailer_burnt_narr = pack_info_lst[
                                                  pack_info_lst.index(i) + 3].split(
                                ":", 1)[-1].lstrip().rstrip() + ":"
                            index_trailer_narr = self.comboNarrTrailer.findText(trailer_burnt_narr,
                                                                                QtCore.Qt.MatchStartsWith)
                            if index_trailer_narr >= 0:
                                self.trailer_narr.setChecked(True)
                                self.comboNarrTrailer.setCurrentIndex(index_trailer_narr)

                        if i.startswith("Feature:"):
                            feat_crop_top_line = pack_info_lst[pack_info_lst.index(i) + 2]
                            if feat_crop_top_line.startswith('<attribute name="crop.top"'):
                                feat_crop_top = ""
                                for character in list(feat_crop_top_line):
                                    if character.isdigit():
                                        feat_crop_top += character
                                self.feat_top_crop.setText(feat_crop_top)

                            feat_crop_bottom_line = pack_info_lst[pack_info_lst.index(i) + 3]
                            if feat_crop_bottom_line.startswith('<attribute name="crop.bottom"'):
                                feat_crop_bottom = ""
                                for character in list(feat_crop_bottom_line):
                                    if character.isdigit():
                                        feat_crop_bottom += character
                                self.feat_bottom_crop.setText(feat_crop_bottom)

                            feat_crop_left_line = pack_info_lst[pack_info_lst.index(i) + 4]
                            if feat_crop_left_line.startswith('<attribute name="crop.left"'):
                                feat_crop_left = ""
                                for character in list(feat_crop_left_line):
                                    if character.isdigit():
                                        feat_crop_left += character
                                self.feat_left_crop.setText(feat_crop_left)

                            feat_crop_right_line = pack_info_lst[pack_info_lst.index(i) + 5]
                            if feat_crop_right_line.startswith('<attribute name="crop.right"'):
                                feat_crop_right = ""
                                for character in list(feat_crop_right_line):
                                    if character.isdigit():
                                        feat_crop_right += character
                                self.feat_right_crop.setText(feat_crop_right)

                        if i.startswith("Trailer:"):
                            trailer_crop_top_line = pack_info_lst[pack_info_lst.index(i) + 2]
                            if trailer_crop_top_line.startswith('<attribute name="crop.top"'):
                                trailer_crop_top = ""
                                for character in list(trailer_crop_top_line):
                                    if character.isdigit():
                                        trailer_crop_top += character
                                self.trailer_top_crop.setText(trailer_crop_top)

                            trailer_crop_bottom_line = pack_info_lst[pack_info_lst.index(i) + 3]
                            if trailer_crop_bottom_line.startswith('<attribute name="crop.bottom"'):
                                trailer_crop_bottom = ""
                                for character in list(trailer_crop_bottom_line):
                                    if character.isdigit():
                                        trailer_crop_bottom += character
                                self.trailer_bottom_crop.setText(trailer_crop_bottom)

                            trailer_crop_left_line = pack_info_lst[pack_info_lst.index(i) + 4]
                            if trailer_crop_left_line.startswith('<attribute name="crop.left"'):
                                trailer_crop_left = ""
                                for character in list(trailer_crop_left_line):
                                    if character.isdigit():
                                        trailer_crop_left += character
                                self.trailer_left_crop.setText(trailer_crop_left)

                            trailer_crop_right_line = pack_info_lst[pack_info_lst.index(i) + 5]
                            if trailer_crop_right_line.startswith('<attribute name="crop.right"'):
                                trailer_crop_right = ""
                                for character in list(trailer_crop_right_line):
                                    if character.isdigit():
                                        trailer_crop_right += character
                                self.trailer_right_crop.setText(trailer_crop_right)

                with codecs.open("package_info.txt", "r", encoding="utf8") as pack_info_lines:
                    settings.chapters_tc = []
                    for line in pack_info_lines:
                        if line.startswith("chap"):
                            chap_tc = line.split()[1]
                            thumb_tc = line.split()[-1]
                            settings.chapters_tc.append(chap_tc)
                            settings.chapter_thumbs.append(thumb_tc)

                            self.chap_tc_display.appendPlainText(chap_tc)
                            self.chap_thumb_display.appendPlainText(thumb_tc)

                        if line.startswith("Trailer/Preview Still"):
                            settings.trailer_still = line.split()[-1]
                            self.trailer_still_tc.setText(settings.trailer_still)

                        if line.startswith("Feature spoken audio"):
                            feature_audio = line.split(":", 1)[-1].lstrip().rstrip() + ":"
                            index_feature_audio = self.comboFeatureAudio.findText(feature_audio,
                                                                                  QtCore.Qt.MatchStartsWith)
                            self.comboFeatureAudio.setCurrentIndex(index_feature_audio)

                        if line.startswith("Trailer spoken audio"):
                            trailer_audio = line.split(":", 1)[-1].lstrip().rstrip() + ":"
                            index_trailer_audio = self.comboTrailerAudio.findText(trailer_audio,
                                                                                  QtCore.Qt.MatchStartsWith)
                            self.comboTrailerAudio.setCurrentIndex(index_trailer_audio)

                settings.chapters_tc.sort()
                settings.chapter_thumbs.sort()
                # self.pack_info_lcd.display(len(settings.chapters_tc))
                self.chapter_thumbs_lcd.display(len(settings.chapter_thumbs))

            except IOError:
                pack_info_msg = QtGui.QMessageBox()

                pack_info_msg.setIcon(QtGui.QMessageBox.Warning)
                pack_info_msg.setText("Error opening file.")
                pack_info_msg.setWindowTitle("Error")
                pack_info_msg.setStandardButtons(QtGui.QMessageBox.Ok)
                pack_info_msg.exec_()

    def set_xml_dest(self):
        settings.destination = str(QtGui.QFileDialog.getExistingDirectory(
                self,
                "Select the destination for the Xml",
                settings.directory))

        settings.directory = settings.destination
        self.xml_dest_lbl.setText(settings.destination)

    def set_build_scenario(self):
        scenario = str(self.build_scenario.currentText())

        if scenario == "Full Package":
            self.build_meta.setCheckState(QtCore.Qt.Unchecked)
            self.build_genres_ratings.setCheckState(QtCore.Qt.Unchecked)
            self.build_cast_crew.setCheckState(QtCore.Qt.Unchecked)
            self.build_feat.setCheckState(QtCore.Qt.Unchecked)
            self.build_feat_assets.setCheckState(QtCore.Qt.Unchecked)
            self.build_chapters.setCheckState(QtCore.Qt.Unchecked)
            self.build_trailer.setCheckState(QtCore.Qt.Unchecked)
            self.build_trailer_assets.setCheckState(QtCore.Qt.Unchecked)
            self.build_poster.setCheckState(QtCore.Qt.Unchecked)
            self.build_product.setCheckState(QtCore.Qt.Unchecked)

            self.build_meta.setCheckState(QtCore.Qt.Checked)
            self.build_genres_ratings.setCheckState(QtCore.Qt.Checked)
            self.build_cast_crew.setCheckState(QtCore.Qt.Checked)
            self.build_feat.setCheckState(QtCore.Qt.Checked)
            self.build_feat_assets.setCheckState(QtCore.Qt.Checked)
            self.build_chapters.setCheckState(QtCore.Qt.Checked)
            self.build_trailer.setCheckState(QtCore.Qt.Checked)
            self.build_trailer_assets.setCheckState(QtCore.Qt.Checked)
            self.build_poster.setCheckState(QtCore.Qt.Checked)
            self.build_product.setCheckState(QtCore.Qt.Checked)

        elif scenario == "Asset Update":
            self.build_meta.setCheckState(QtCore.Qt.Unchecked)
            self.build_genres_ratings.setCheckState(QtCore.Qt.Unchecked)
            self.build_cast_crew.setCheckState(QtCore.Qt.Unchecked)
            self.build_feat.setCheckState(QtCore.Qt.Unchecked)
            self.build_feat_assets.setCheckState(QtCore.Qt.Unchecked)
            self.build_chapters.setCheckState(QtCore.Qt.Unchecked)
            self.build_trailer.setCheckState(QtCore.Qt.Unchecked)
            self.build_trailer_assets.setCheckState(QtCore.Qt.Unchecked)
            self.build_poster.setCheckState(QtCore.Qt.Unchecked)
            self.build_product.setCheckState(QtCore.Qt.Unchecked)

            self.build_feat.setCheckState(QtCore.Qt.Checked)
            self.build_feat_assets.setCheckState(QtCore.Qt.Checked)
            self.build_chapters.setCheckState(QtCore.Qt.Checked)
            self.build_trailer.setCheckState(QtCore.Qt.Checked)
            self.build_trailer_assets.setCheckState(QtCore.Qt.Checked)

        elif scenario == "Assetless preorder":
            self.build_meta.setCheckState(QtCore.Qt.Unchecked)
            self.build_genres_ratings.setCheckState(QtCore.Qt.Unchecked)
            self.build_cast_crew.setCheckState(QtCore.Qt.Unchecked)
            self.build_feat.setCheckState(QtCore.Qt.Unchecked)
            self.build_feat_assets.setCheckState(QtCore.Qt.Unchecked)
            self.build_chapters.setCheckState(QtCore.Qt.Unchecked)
            self.build_trailer.setCheckState(QtCore.Qt.Unchecked)
            self.build_trailer_assets.setCheckState(QtCore.Qt.Unchecked)
            self.build_poster.setCheckState(QtCore.Qt.Unchecked)
            self.build_product.setCheckState(QtCore.Qt.Unchecked)

            self.build_meta.setCheckState(QtCore.Qt.Checked)
            self.build_genres_ratings.setCheckState(QtCore.Qt.Checked)
            self.build_cast_crew.setCheckState(QtCore.Qt.Checked)
            self.build_trailer.setCheckState(QtCore.Qt.Checked)
            self.build_trailer_assets.setCheckState(QtCore.Qt.Checked)
            self.build_poster.setCheckState(QtCore.Qt.Checked)
            self.build_product.setCheckState(QtCore.Qt.Checked)

    def process(self):
        if settings.destination == "":
            path_msg = QtGui.QMessageBox()

            path_msg.setIcon(QtGui.QMessageBox.Information)
            path_msg.setText("Please select a destination for the Xml.")
            path_msg.setWindowTitle("Input needed")
            path_msg.setStandardButtons(QtGui.QMessageBox.Ok)
            path_msg.exec_()
            return

        else:
            if not any([
                self.build_meta.isChecked(),
                self.build_genres_ratings.isChecked(),
                self.build_cast_crew.isChecked(),
                self.build_feat.isChecked(),
                self.build_feat_assets.isChecked(),
                self.build_chapters.isChecked(),
                self.build_trailer.isChecked(),
                self.build_trailer_assets.isChecked(),
                self.build_poster.isChecked(),
                self.build_product.isChecked(),
                self.build_loc_trailer.isChecked(),
                self.build_loc_trailer_assets.isChecked()
            ]):
                check_msg = QtGui.QMessageBox()

                check_msg.setIcon(QtGui.QMessageBox.Information)
                check_msg.setText("Please select at least one element to include in the xml.")
                check_msg.setWindowTitle("Input needed")
                check_msg.setStandardButtons(QtGui.QMessageBox.Ok)
                check_msg.exec_()
                return
            
            else:
                os.chdir(settings.destination)

                if os.path.isfile("metadata.xml"):
                    file_msg = QtGui.QMessageBox()

                    file_msg.setIcon(QtGui.QMessageBox.Warning)
                    file_msg.setText("<b>WARNING:</b> You are about to <b>overwrite</b> a metadata file. Proceed?")
                    file_msg.setWindowTitle("Overwrite warning")
                    file_msg.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel)
                    outcome = file_msg.exec_()

                    if outcome == QtGui.QMessageBox.Cancel:
                        return

                self.process_stop_btn.setEnabled(True)
                self.process_btn.setEnabled(False)
                self.results_lbl.setText("")

                settings.meta = self.build_meta.isChecked()
                settings.genres_ratings = self.build_genres_ratings.isChecked()
                settings.cast_crew = self.build_cast_crew.isChecked()
                settings.feature = self.build_feat.isChecked()
                settings.feature_assets = self.build_feat_assets.isChecked()
                settings.chapters = self.build_chapters.isChecked()
                settings.trailer = self.build_trailer.isChecked()
                settings.trailer_assets = self.build_trailer_assets.isChecked()
                settings.poster = self.build_poster.isChecked()
                settings.product = self.build_product.isChecked()
                settings.loc_trailer = self.build_loc_trailer.isChecked()
                settings.loc_trailer_assets = self.build_loc_trailer_assets.isChecked()

                if settings.meta:
                    self.tabWidget.tabBar().setTabTextColor(8, QtCore.Qt.red)
                    self.tabWidget.tabBar().setTabTextColor(12, QtCore.Qt.red)

                if settings.genres_ratings:
                    self.tabWidget.tabBar().setTabTextColor(9, QtCore.Qt.red)

                if settings.cast_crew:
                    self.tabWidget.tabBar().setTabTextColor(10, QtCore.Qt.red)
                    self.tabWidget.tabBar().setTabTextColor(11, QtCore.Qt.red)

                if settings.feature:
                    self.tabWidget.tabBar().setTabTextColor(1, QtCore.Qt.red)

                if settings.feature_assets:
                    self.tabWidget.tabBar().setTabTextColor(2, QtCore.Qt.red)

                if settings.chapters:
                    self.tabWidget.tabBar().setTabTextColor(3, QtCore.Qt.red)
                    settings.chapters_done = False

                if settings.trailer:
                    self.tabWidget.tabBar().setTabTextColor(4, QtCore.Qt.red)

                if settings.trailer_assets:
                    self.tabWidget.tabBar().setTabTextColor(5, QtCore.Qt.red)

                if settings.poster:
                    self.tabWidget.tabBar().setTabTextColor(6, QtCore.Qt.red)

                if settings.product:
                    self.tabWidget.tabBar().setTabTextColor(7, QtCore.Qt.red)

                if settings.loc_trailer:
                    self.tabWidget.tabBar().setTabTextColor(13, QtCore.Qt.red)

                if settings.loc_trailer_assets:
                    self.tabWidget.tabBar().setTabTextColor(14, QtCore.Qt.red)

                self.tabWidget.tabBar().setTabTextColor(0, QtCore.Qt.red)

                self.results_lbl.setText("Generating Xml...")
                self.process_progress.setRange(0, 0)
                self.connect(self.create_xml_thread, QtCore.SIGNAL("meta_done"), self.meta_done)
                self.connect(self.create_xml_thread, QtCore.SIGNAL("genres_ratings_done"), self.genres_ratings_done)
                self.connect(self.create_xml_thread, QtCore.SIGNAL("cast_crew_done"), self.cast_crew_done)
                self.connect(self.create_xml_thread, QtCore.SIGNAL("chapters_done"), self.chapters_done)
                self.connect(self.create_xml_thread, QtCore.SIGNAL("feature_done"), self.feature_done)
                self.connect(self.create_xml_thread, QtCore.SIGNAL("feature_assets_done"), self.feature_assets_done)
                self.connect(self.create_xml_thread, QtCore.SIGNAL("trailer_done"), self.trailer_done)
                self.connect(self.create_xml_thread, QtCore.SIGNAL("trailer_assets_done"), self.trailer_assets_done)
                self.connect(self.create_xml_thread, QtCore.SIGNAL("poster_done"), self.poster_done)
                self.connect(self.create_xml_thread, QtCore.SIGNAL("product_done"), self.product_done)
                self.connect(self.create_xml_thread, QtCore.SIGNAL("finished()"), self.create_xml_done)
                self.connect(self.create_xml_thread, QtCore.SIGNAL("loc_trailer_done"), self.loc_trailer_done)
                self.connect(self.create_xml_thread, QtCore.SIGNAL("loc_trailer_assets_done"),
                             self.loc_trailer_assets_done)
                self.create_xml_thread.start()

    def meta_done(self):
        self.tabWidget.tabBar().setTabTextColor(8, QtCore.Qt.black)
        self.tabWidget.tabBar().setTabTextColor(12, QtCore.Qt.black)

    def genres_ratings_done(self):
        self.tabWidget.tabBar().setTabTextColor(9, QtCore.Qt.black)

    def cast_crew_done(self):
        self.tabWidget.tabBar().setTabTextColor(10, QtCore.Qt.black)
        self.tabWidget.tabBar().setTabTextColor(11, QtCore.Qt.black)

    def chapters_done(self):
        self.tabWidget.tabBar().setTabTextColor(3, QtCore.Qt.black)

    def feature_done(self):
        self.tabWidget.tabBar().setTabTextColor(1, QtCore.Qt.black)

    def feature_assets_done(self):
        self.tabWidget.tabBar().setTabTextColor(2, QtCore.Qt.black)

    def trailer_done(self):
        self.tabWidget.tabBar().setTabTextColor(4, QtCore.Qt.black)

    def trailer_assets_done(self):
        self.tabWidget.tabBar().setTabTextColor(5, QtCore.Qt.black)

    def poster_done(self):
        self.tabWidget.tabBar().setTabTextColor(6, QtCore.Qt.black)

    def product_done(self):
        self.tabWidget.tabBar().setTabTextColor(7, QtCore.Qt.black)

    def loc_trailer_done(self):
        self.tabWidget.tabBar().setTabTextColor(13, QtCore.Qt.black)

    def loc_trailer_assets_done(self):
        self.tabWidget.tabBar().setTabTextColor(14, QtCore.Qt.black)

    def create_xml_done(self):
        self.process_stop_btn.setEnabled(False)
        self.process_btn.setEnabled(True)
        self.process_progress.setRange(0, 1)
        self.process_progress.setValue(1)
        self.tabWidget.tabBar().setTabTextColor(0, QtCore.Qt.black)
        results = "Xml generated at %s." % time.strftime("%X")
        self.results_lbl.setText(results)
        self.validation_results.setPlainText(settings.results)

    def stop_process(self):
        self.create_xml_thread.terminate()
        self.process_stop_btn.setEnabled(False)
        self.process_btn.setEnabled(True)
        self.process_progress.setRange(0, 1)
        self.process_progress.setValue(0)
        self.tabWidget.tabBar().setTabTextColor(0, QtCore.Qt.black)
        self.tabWidget.tabBar().setTabTextColor(1, QtCore.Qt.black)
        self.tabWidget.tabBar().setTabTextColor(2, QtCore.Qt.black)
        self.tabWidget.tabBar().setTabTextColor(3, QtCore.Qt.black)
        self.tabWidget.tabBar().setTabTextColor(4, QtCore.Qt.black)
        self.tabWidget.tabBar().setTabTextColor(5, QtCore.Qt.black)
        self.tabWidget.tabBar().setTabTextColor(6, QtCore.Qt.black)
        self.tabWidget.tabBar().setTabTextColor(7, QtCore.Qt.black)
        self.tabWidget.tabBar().setTabTextColor(8, QtCore.Qt.black)
        self.tabWidget.tabBar().setTabTextColor(9, QtCore.Qt.black)
        self.tabWidget.tabBar().setTabTextColor(10, QtCore.Qt.black)
        self.tabWidget.tabBar().setTabTextColor(11, QtCore.Qt.black)
        self.tabWidget.tabBar().setTabTextColor(13, QtCore.Qt.black)
        self.tabWidget.tabBar().setTabTextColor(14, QtCore.Qt.black)
        results = "Process stopped."
        self.results_lbl.setText(results)

    def reset_app(self):
        reset_msg = QtGui.QMessageBox()
    
        reset_msg.setIcon(QtGui.QMessageBox.Warning)
        reset_msg.setText("<b>WARNING:</b> You are about to <b>reset</b> all values. Proceed?")
        reset_msg.setWindowTitle("Reset warning")
        reset_msg.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel)
        outcome = reset_msg.exec_()
    
        if outcome == QtGui.QMessageBox.Cancel:
            return
    
        else:
            # metadata
            index_country = self.comboCountry.findText("UNITED STATES: US", QtCore.Qt.MatchFixedString)
            self.comboCountry.setCurrentIndex(index_country)
            index_original_locale = self.comboOriginalLanguage.findText("en-US: English (United States)",
                                                                        QtCore.Qt.MatchFixedString)
            self.comboOriginalLanguage.setCurrentIndex(index_original_locale)

            self.adapted_title.setText("")
            self.release_title.setText("")
            self.synopsis.setPlainText("")
            self.production.setText("")
            self.copyright.setText("")
            self.theatrical.setText("")

            # genres and ratings
            index_genre1 = self.genre1.findText("", QtCore.Qt.MatchFixedString)
            self.genre1.setCurrentIndex(index_genre1)

            index_genre2 = self.genre2.findText("", QtCore.Qt.MatchFixedString)
            self.genre2.setCurrentIndex(index_genre2)

            index_genre3 = self.genre3.findText("", QtCore.Qt.MatchFixedString)
            self.genre3.setCurrentIndex(index_genre3)

            index_genre4 = self.genre4.findText("", QtCore.Qt.MatchFixedString)
            self.genre4.setCurrentIndex(index_genre4)

            index_genre5 = self.genre5.findText("", QtCore.Qt.MatchFixedString)
            self.genre5.setCurrentIndex(index_genre5)

            index_genre6 = self.genre6.findText("", QtCore.Qt.MatchFixedString)
            self.genre6.setCurrentIndex(index_genre6)

            index_genre7 = self.genre7.findText("", QtCore.Qt.MatchFixedString)
            self.genre7.setCurrentIndex(index_genre7)

            index_genre8 = self.genre8.findText("", QtCore.Qt.MatchFixedString)
            self.genre8.setCurrentIndex(index_genre8)

            # ratings
            index_rating1_sys = self.rating1_sys.findText("", QtCore.Qt.MatchFixedString)
            self.rating1_sys.setCurrentIndex(index_rating1_sys)

            index_rating2_sys = self.rating2_sys.findText("", QtCore.Qt.MatchFixedString)
            self.rating2_sys.setCurrentIndex(index_rating2_sys)

            index_rating3_sys = self.rating3_sys.findText("", QtCore.Qt.MatchFixedString)
            self.rating3_sys.setCurrentIndex(index_rating3_sys)

            index_rating4_sys = self.rating4_sys.findText("", QtCore.Qt.MatchFixedString)
            self.rating4_sys.setCurrentIndex(index_rating4_sys)

            index_rating5_sys = self.rating5_sys.findText("", QtCore.Qt.MatchFixedString)
            self.rating5_sys.setCurrentIndex(index_rating5_sys)

            self.rating1_value.setText("")
            self.rating2_value.setText("")
            self.rating3_value.setText("")
            self.rating4_value.setText("")
            self.rating5_value.setText("")

            # cast
            self.actor1_name.setText("")
            self.actor2_name.setText("")
            self.actor3_name.setText("")
            self.actor4_name.setText("")
            self.actor5_name.setText("")
            self.actor6_name.setText("")
            self.actor7_name.setText("")
            self.actor8_name.setText("")
            self.actor9_name.setText("")
            self.actor10_name.setText("")

            self.actor1_apple_id.setText("")
            self.actor2_apple_id.setText("")
            self.actor3_apple_id.setText("")
            self.actor4_apple_id.setText("")
            self.actor5_apple_id.setText("")
            self.actor6_apple_id.setText("")
            self.actor7_apple_id.setText("")
            self.actor8_apple_id.setText("")
            self.actor9_apple_id.setText("")
            self.actor10_apple_id.setText("")

            self.actor1_char.setText("")
            self.actor2_char.setText("")
            self.actor3_char.setText("")
            self.actor4_char.setText("")
            self.actor5_char.setText("")
            self.actor6_char.setText("")
            self.actor7_char.setText("")
            self.actor8_char.setText("")
            self.actor9_char.setText("")
            self.actor10_char.setText("")

            self.actor1_char2.setText("")
            self.actor2_char2.setText("")
            self.actor3_char2.setText("")
            self.actor4_char2.setText("")
            self.actor5_char2.setText("")
            self.actor6_char2.setText("")
            self.actor7_char2.setText("")
            self.actor8_char2.setText("")
            self.actor9_char2.setText("")
            self.actor10_char2.setText("")

            self.actor1_ref.setText("")
            self.actor2_ref.setText("")
            self.actor3_ref.setText("")
            self.actor4_ref.setText("")
            self.actor5_ref.setText("")
            self.actor6_ref.setText("")
            self.actor7_ref.setText("")
            self.actor8_ref.setText("")
            self.actor9_ref.setText("")
            self.actor10_ref.setText("")

            self.actor1_ref2.setText("")
            self.actor2_ref2.setText("")
            self.actor3_ref2.setText("")
            self.actor4_ref2.setText("")
            self.actor5_ref2.setText("")
            self.actor6_ref2.setText("")
            self.actor7_ref2.setText("")
            self.actor8_ref2.setText("")
            self.actor9_ref2.setText("")
            self.actor10_ref2.setText("")

            # crew
            self.crew1_name.setText("")
            self.crew2_name.setText("")
            self.crew3_name.setText("")
            self.crew4_name.setText("")
            self.crew5_name.setText("")
            self.crew6_name.setText("")
            self.crew7_name.setText("")
            self.crew8_name.setText("")
            self.crew9_name.setText("")
            self.crew10_name.setText("")

            self.crew1_apple_id.setText("")
            self.crew2_apple_id.setText("")
            self.crew3_apple_id.setText("")
            self.crew4_apple_id.setText("")
            self.crew5_apple_id.setText("")
            self.crew6_apple_id.setText("")
            self.crew7_apple_id.setText("")
            self.crew8_apple_id.setText("")
            self.crew9_apple_id.setText("")
            self.crew10_apple_id.setText("")

            self.crew1_director.setChecked(False)
            self.crew1_producer.setChecked(False)
            self.crew1_screenwriter.setChecked(False)
            self.crew1_composer.setChecked(False)
            self.crew1_codirector.setChecked(False)

            self.crew2_director.setChecked(False)
            self.crew2_producer.setChecked(False)
            self.crew2_screenwriter.setChecked(False)
            self.crew2_composer.setChecked(False)
            self.crew2_codirector.setChecked(False)

            self.crew3_director.setChecked(False)
            self.crew3_producer.setChecked(False)
            self.crew3_screenwriter.setChecked(False)
            self.crew3_composer.setChecked(False)
            self.crew3_codirector.setChecked(False)

            self.crew4_director.setChecked(False)
            self.crew4_producer.setChecked(False)
            self.crew4_screenwriter.setChecked(False)
            self.crew4_composer.setChecked(False)
            self.crew4_codirector.setChecked(False)

            self.crew5_director.setChecked(False)
            self.crew5_producer.setChecked(False)
            self.crew5_screenwriter.setChecked(False)
            self.crew5_composer.setChecked(False)
            self.crew5_codirector.setChecked(False)

            self.crew6_director.setChecked(False)
            self.crew6_producer.setChecked(False)
            self.crew6_screenwriter.setChecked(False)
            self.crew6_composer.setChecked(False)
            self.crew6_codirector.setChecked(False)

            self.crew7_director.setChecked(False)
            self.crew7_producer.setChecked(False)
            self.crew7_screenwriter.setChecked(False)
            self.crew7_composer.setChecked(False)
            self.crew7_codirector.setChecked(False)

            self.crew8_director.setChecked(False)
            self.crew8_producer.setChecked(False)
            self.crew8_screenwriter.setChecked(False)
            self.crew8_composer.setChecked(False)
            self.crew8_codirector.setChecked(False)

            self.crew9_director.setChecked(False)
            self.crew9_producer.setChecked(False)
            self.crew9_screenwriter.setChecked(False)
            self.crew9_composer.setChecked(False)
            self.crew9_codirector.setChecked(False)

            self.crew10_director.setChecked(False)
            self.crew10_producer.setChecked(False)
            self.crew10_screenwriter.setChecked(False)
            self.crew10_composer.setChecked(False)
            self.crew10_codirector.setChecked(False)

            # feature
            index_feature_audio = self.comboFeatureAudio.findText("en-US: English (United States)", QtCore.Qt.MatchFixedString)
            self.comboFeatureAudio.setCurrentIndex(index_feature_audio)

            index_feature_narr = self.comboNarrFeature.findText("en-US: English (United States)", QtCore.Qt.MatchFixedString)
            self.comboNarrFeature.setCurrentIndex(index_feature_narr)

            index_feature_subs = self.comboSubFeature.findText("en-US: English (United States)", QtCore.Qt.MatchFixedString)
            self.comboSubFeature.setCurrentIndex(index_feature_subs)

            self.feat_top_crop.setText("")
            self.feat_bottom_crop.setText("")
            self.feat_left_crop.setText("")
            self.feat_right_crop.setText("")

            self.feat_md5_lbl.setText("")

            self.feat_narratives.setChecked(False)
            self.feat_subs.setChecked(False)

            # chapters
            index_tc_format = self.tc_format.findText("23.98fps", QtCore.Qt.MatchFixedString)
            self.tc_format.setCurrentIndex(index_tc_format)

            index_chapter_locale = self.chapter_locale_cb_main.findText("en-US: English (United States)", QtCore.Qt.MatchFixedString)
            self.chapter_locale_cb_main.setCurrentIndex(index_chapter_locale)

            self.chap_01_tc_ln.setText("")
            self.chap_02_tc_ln.setText("")
            self.chap_03_tc_ln.setText("")
            self.chap_04_tc_ln.setText("")
            self.chap_05_tc_ln.setText("")
            self.chap_06_tc_ln.setText("")
            self.chap_07_tc_ln.setText("")
            self.chap_08_tc_ln.setText("")
            self.chap_09_tc_ln.setText("")
            self.chap_10_tc_ln.setText("")
            self.chap_11_tc_ln.setText("")
            self.chap_12_tc_ln.setText("")
            self.chap_13_tc_ln.setText("")
            self.chap_14_tc_ln.setText("")
            self.chap_15_tc_ln.setText("")
            self.chap_16_tc_ln.setText("")
            self.chap_17_tc_ln.setText("")
            self.chap_18_tc_ln.setText("")
            self.chap_19_tc_ln.setText("")
            self.chap_20_tc_ln.setText("")

            self.chap_01_thumb_tc_ln.setText("")
            self.chap_02_thumb_tc_ln.setText("")
            self.chap_03_thumb_tc_ln.setText("")
            self.chap_04_thumb_tc_ln.setText("")
            self.chap_05_thumb_tc_ln.setText("")
            self.chap_06_thumb_tc_ln.setText("")
            self.chap_07_thumb_tc_ln.setText("")
            self.chap_08_thumb_tc_ln.setText("")
            self.chap_09_thumb_tc_ln.setText("")
            self.chap_10_thumb_tc_ln.setText("")
            self.chap_11_thumb_tc_ln.setText("")
            self.chap_12_thumb_tc_ln.setText("")
            self.chap_13_thumb_tc_ln.setText("")
            self.chap_14_thumb_tc_ln.setText("")
            self.chap_15_thumb_tc_ln.setText("")
            self.chap_16_thumb_tc_ln.setText("")
            self.chap_17_thumb_tc_ln.setText("")
            self.chap_18_thumb_tc_ln.setText("")
            self.chap_19_thumb_tc_ln.setText("")
            self.chap_20_thumb_tc_ln.setText("")

            while self.chapter_title_lyt.count() > 0:
                self.chap_locale_del()

            settings.chapters_tc.clear()
            settings.thumbs_tc.clear()

            # trailer
            index_trailer_audio = self.comboTrailerAudio.findText("en-US: English (United States)", QtCore.Qt.MatchFixedString)
            self.comboTrailerAudio.setCurrentIndex(index_trailer_audio)

            index_trailer_narr = self.comboNarrTrailer.findText("en-US: English (United States)", QtCore.Qt.MatchFixedString)
            self.comboNarrTrailer.setCurrentIndex(index_trailer_narr)

            index_trailer_subs = self.comboSubTrailer.findText("en-US: English (United States)", QtCore.Qt.MatchFixedString)
            self.comboSubTrailer.setCurrentIndex(index_trailer_subs)

            index_tc_format_ww_trailer = self.tc_format_ww_trailer.findText("23.98fps", QtCore.Qt.MatchFixedString)
            self.tc_format_ww_trailer.setCurrentIndex(index_tc_format_ww_trailer)

            self.trailer_still_tc.setText("")
            self.trailer_top_crop.setText("")
            self.trailer_bottom_crop.setText("")
            self.trailer_left_crop.setText("")
            self.trailer_right_crop.setText("")

            self.trailer_md5_lbl.setText("")

            self.trailer_narr.setChecked(False)
            self.trailer_subs.setChecked(False)

            # feature assets
            self.feat_asset1_role.clear()
            self.feat_asset1_role.addItems(settings.data_roles)

            index_feat_asset1_locale = self.feat_asset1_locale.findText("en-US: English (United States)",
                                                                        QtCore.Qt.MatchFixedString)
            self.feat_asset1_locale.setCurrentIndex(index_feat_asset1_locale)

            self.feat_asset2_role.clear()
            self.feat_asset2_role.addItems(settings.data_roles)

            index_feat_asset2_locale = self.feat_asset2_locale.findText("en-US: English (United States)",
                                                                        QtCore.Qt.MatchFixedString)
            self.feat_asset2_locale.setCurrentIndex(index_feat_asset2_locale)

            self.feat_asset3_role.clear()
            self.feat_asset3_role.addItems(settings.data_roles)

            index_feat_asset3_locale = self.feat_asset3_locale.findText("en-US: English (United States)",
                                                                        QtCore.Qt.MatchFixedString)
            self.feat_asset3_locale.setCurrentIndex(index_feat_asset3_locale)

            self.feat_asset4_role.clear()
            self.feat_asset4_role.addItems(settings.data_roles)

            index_feat_asset4_locale = self.feat_asset4_locale.findText("en-US: English (United States)",
                                                                        QtCore.Qt.MatchFixedString)
            self.feat_asset4_locale.setCurrentIndex(index_feat_asset4_locale)

            self.feat_asset5_role.clear()
            self.feat_asset5_role.addItems(settings.data_roles)

            index_feat_asset5_locale = self.feat_asset5_locale.findText("en-US: English (United States)",
                                                                        QtCore.Qt.MatchFixedString)
            self.feat_asset5_locale.setCurrentIndex(index_feat_asset5_locale)

            self.feat_asset6_role.clear()
            self.feat_asset6_role.addItems(settings.data_roles)

            index_feat_asset6_locale = self.feat_asset6_locale.findText("en-US: English (United States)",
                                                                        QtCore.Qt.MatchFixedString)
            self.feat_asset6_locale.setCurrentIndex(index_feat_asset6_locale)

            self.feat_asset7_role.clear()
            self.feat_asset7_role.addItems(settings.data_roles)

            index_feat_asset7_locale = self.feat_asset7_locale.findText("en-US: English (United States)",
                                                                        QtCore.Qt.MatchFixedString)
            self.feat_asset7_locale.setCurrentIndex(index_feat_asset7_locale)

            self.feat_asset8_role.clear()
            self.feat_asset8_role.addItems(settings.data_roles)

            index_feat_asset8_locale = self.feat_asset8_locale.findText("en-US: English (United States)",
                                                                        QtCore.Qt.MatchFixedString)
            self.feat_asset8_locale.setCurrentIndex(index_feat_asset8_locale)

            while self.feat_asset1_lyt.count() > 0:
                self.feat_asset1_del()

            while self.feat_asset2_lyt.count() > 0:
                self.feat_asset2_del()

            while self.feat_asset3_lyt.count() > 0:
                self.feat_asset3_del()

            while self.feat_asset4_lyt.count() > 0:
                self.feat_asset4_del()

            while self.feat_asset5_lyt.count() > 0:
                self.feat_asset5_del()

            while self.feat_asset6_lyt.count() > 0:
                self.feat_asset6_del()

            while self.feat_asset7_lyt.count() > 0:
                self.feat_asset7_del()

            while self.feat_asset8_lyt.count() > 0:
                self.feat_asset8_del()

            # trailer assets
            self.trailer_asset1_role.clear()
            self.trailer_asset1_role.addItems(settings.data_roles)

            index_trailer_asset1_locale = self.trailer_asset1_locale.findText("en-US: English (United States)",
                                                                              QtCore.Qt.MatchFixedString)
            self.trailer_asset1_locale.setCurrentIndex(index_trailer_asset1_locale)

            self.trailer_asset2_role.clear()
            self.trailer_asset2_role.addItems(settings.data_roles)

            index_trailer_asset2_locale = self.trailer_asset2_locale.findText("en-US: English (United States)",
                                                                              QtCore.Qt.MatchFixedString)
            self.trailer_asset2_locale.setCurrentIndex(index_trailer_asset2_locale)

            self.trailer_asset3_role.clear()
            self.trailer_asset3_role.addItems(settings.data_roles)

            index_trailer_asset3_locale = self.trailer_asset3_locale.findText("en-US: English (United States)",
                                                                              QtCore.Qt.MatchFixedString)
            self.trailer_asset3_locale.setCurrentIndex(index_trailer_asset3_locale)

            self.trailer_asset4_role.clear()
            self.trailer_asset4_role.addItems(settings.data_roles)

            index_trailer_asset4_locale = self.trailer_asset4_locale.findText("en-US: English (United States)",
                                                                              QtCore.Qt.MatchFixedString)
            self.trailer_asset4_locale.setCurrentIndex(index_trailer_asset4_locale)

            self.trailer_asset5_role.clear()
            self.trailer_asset5_role.addItems(settings.data_roles)

            index_trailer_asset5_locale = self.trailer_asset5_locale.findText("en-US: English (United States)",
                                                                              QtCore.Qt.MatchFixedString)
            self.trailer_asset5_locale.setCurrentIndex(index_trailer_asset5_locale)

            self.trailer_asset6_role.clear()
            self.trailer_asset6_role.addItems(settings.data_roles)

            index_trailer_asset6_locale = self.trailer_asset6_locale.findText("en-US: English (United States)",
                                                                              QtCore.Qt.MatchFixedString)
            self.trailer_asset6_locale.setCurrentIndex(index_trailer_asset6_locale)

            self.trailer_asset7_role.clear()
            self.trailer_asset7_role.addItems(settings.data_roles)

            index_trailer_asset7_locale = self.trailer_asset7_locale.findText("en-US: English (United States)",
                                                                              QtCore.Qt.MatchFixedString)
            self.trailer_asset7_locale.setCurrentIndex(index_trailer_asset7_locale)

            self.trailer_asset8_role.clear()
            self.trailer_asset8_role.addItems(settings.data_roles)

            index_trailer_asset8_locale = self.trailer_asset8_locale.findText("en-US: English (United States)",
                                                                              QtCore.Qt.MatchFixedString)
            self.trailer_asset8_locale.setCurrentIndex(index_trailer_asset8_locale)

            # poster
            index_poster_locale = self.comboPoster.findText("en-US: English (United States)", QtCore.Qt.MatchFixedString)
            self.comboPoster.setCurrentIndex(index_poster_locale)

            # product
            self.product1_check.setChecked(False)
            self.product2_check.setChecked(False)
            self.product3_check.setChecked(False)
            self.product4_check.setChecked(False)

            self.product1_sales_start_check.setChecked(True)
            self.product2_sales_start_check.setChecked(True)
            self.product3_sales_start_check.setChecked(True)
            self.product4_sales_start_check.setChecked(True)

            self.product1_sales_end_check.setChecked(True)
            self.product2_sales_end_check.setChecked(True)
            self.product3_sales_end_check.setChecked(True)
            self.product4_sales_end_check.setChecked(True)

            self.product1_preorder_check.setChecked(True)
            self.product2_preorder_check.setChecked(True)
            self.product3_preorder_check.setChecked(True)
            self.product4_preorder_check.setChecked(True)

            self.product1_vod_start_check.setChecked(True)
            self.product2_vod_start_check.setChecked(True)
            self.product3_vod_start_check.setChecked(True)
            self.product4_vod_start_check.setChecked(True)

            self.product1_vod_end_check.setChecked(True)
            self.product2_vod_end_check.setChecked(True)
            self.product3_vod_end_check.setChecked(True)
            self.product4_vod_end_check.setChecked(True)

            self.product1_physical_check.setChecked(True)
            self.product2_physical_check.setChecked(True)
            self.product3_physical_check.setChecked(True)
            self.product4_physical_check.setChecked(True)

            self.product1_price_sd_check.setChecked(True)
            self.product2_price_sd_check.setChecked(True)
            self.product3_price_sd_check.setChecked(True)
            self.product4_price_sd_check.setChecked(True)

            self.product1_price_hd_check.setChecked(True)
            self.product2_price_hd_check.setChecked(True)
            self.product3_price_hd_check.setChecked(True)
            self.product4_price_hd_check.setChecked(True)

            self.product1_vod_type_check.setChecked(True)
            self.product2_vod_type_check.setChecked(True)
            self.product3_vod_type_check.setChecked(True)
            self.product4_vod_type_check.setChecked(True)

            index_product1_terr = self.product1_terr.findText("US", QtCore.Qt.MatchFixedString)
            self.product1_terr.setCurrentIndex(index_product1_terr)

            self.product1_sale_clear.clear()
            self.product1_sale_clear.addItems(settings.cleared_choices)

            self.product1_price_sd.setText("")
            self.product1_price_hd.setText("")

            self.product1_sales_start.setText("")
            self.product1_sales_end.setText("")
            self.product1_preorder.setText("")

            self.product1_vod_clear.clear()
            self.product1_vod_clear.addItems(settings.cleared_choices)

            self.product1_vod_type.clear()
            self.product1_vod_type.addItems(settings.vod_types)

            self.product1_vod_start.setText("")
            self.product1_vod_end.setText("")
            self.product1_physical.setText("")

            index_product2_terr = self.product2_terr.findText("US", QtCore.Qt.MatchFixedString)
            self.product2_terr.setCurrentIndex(index_product2_terr)

            self.product2_sale_clear.clear()
            self.product2_sale_clear.addItems(settings.cleared_choices)

            self.product2_price_sd.setText("")
            self.product2_price_hd.setText("")

            self.product2_sales_start.setText("")
            self.product2_sales_end.setText("")
            self.product2_preorder.setText("")

            self.product2_vod_clear.clear()
            self.product2_vod_clear.addItems(settings.cleared_choices)

            self.product2_vod_type.clear()
            self.product2_vod_type.addItems(settings.vod_types)

            self.product2_vod_start.setText("")
            self.product2_vod_end.setText("")
            self.product2_physical.setText("")

            index_product3_terr = self.product3_terr.findText("US", QtCore.Qt.MatchFixedString)
            self.product3_terr.setCurrentIndex(index_product3_terr)

            self.product3_sale_clear.clear()
            self.product3_sale_clear.addItems(settings.cleared_choices)

            self.product3_price_sd.setText("")
            self.product3_price_hd.setText("")

            self.product3_sales_start.setText("")
            self.product3_sales_end.setText("")
            self.product3_preorder.setText("")

            self.product3_vod_clear.clear()
            self.product3_vod_clear.addItems(settings.cleared_choices)

            self.product3_vod_type.clear()
            self.product3_vod_type.addItems(settings.vod_types)

            self.product3_vod_start.setText("")
            self.product3_vod_end.setText("")
            self.product3_physical.setText("")

            index_product4_terr = self.product4_terr.findText("US", QtCore.Qt.MatchFixedString)
            self.product4_terr.setCurrentIndex(index_product4_terr)

            self.product4_sale_clear.clear()
            self.product4_sale_clear.addItems(settings.cleared_choices)

            self.product4_price_sd.setText("")
            self.product4_price_hd.setText("")

            self.product4_sales_start.setText("")
            self.product4_sales_end.setText("")
            self.product4_preorder.setText("")

            self.product4_vod_clear.clear()
            self.product4_vod_clear.addItems(settings.cleared_choices)

            self.product4_vod_type.clear()
            self.product4_vod_type.addItems(settings.vod_types)

            self.product4_vod_start.setText("")
            self.product4_vod_end.setText("")
            self.product4_physical.setText("")

            # localization
            self.localized_check_1.setChecked(False)
            index_localized_locale_1 = self.localized_locale_1.findText("en-US: English (United States)",
                                                                        QtCore.Qt.MatchFixedString)
            self.localized_locale_1.setCurrentIndex(index_localized_locale_1)
            self.localized_title_1.setText("")
            self.localized_synopsis_1.setPlainText("")

            self.localized_check_2.setChecked(False)
            index_localized_locale_2 = self.localized_locale_2.findText("en-US: English (United States)",
                                                                        QtCore.Qt.MatchFixedString)
            self.localized_locale_2.setCurrentIndex(index_localized_locale_2)
            self.localized_title_2.setText("")
            self.localized_synopsis_2.setPlainText("")

            self.localized_check_3.setChecked(False)
            index_localized_locale_3 = self.localized_locale_3.findText("en-US: English (United States)",
                                                                        QtCore.Qt.MatchFixedString)
            self.localized_locale_3.setCurrentIndex(index_localized_locale_3)
            self.localized_title_3.setText("")
            self.localized_synopsis_3.setPlainText("")

            self.localized_check_4.setChecked(False)
            index_localized_locale_4 = self.localized_locale_4.findText("en-US: English (United States)",
                                                                        QtCore.Qt.MatchFixedString)
            self.localized_locale_4.setCurrentIndex(index_localized_locale_4)
            self.localized_title_4.setText("")
            self.localized_synopsis_4.setPlainText("")

            # localized trailer
            index_loc_trailer_audio = self.loc_comboTrailerAudio.findText("en-US: English (United States)",
                                                                  QtCore.Qt.MatchFixedString)
            self.loc_comboTrailerAudio.setCurrentIndex(index_loc_trailer_audio)

            index_loc_trailer_narr = self.loc_comboNarrTrailer.findText("en-US: English (United States)",
                                                                QtCore.Qt.MatchFixedString)
            self.loc_comboNarrTrailer.setCurrentIndex(index_loc_trailer_narr)

            index_loc_trailer_subs = self.loc_comboSubTrailer.findText("en-US: English (United States)",
                                                               QtCore.Qt.MatchFixedString)
            self.loc_comboSubTrailer.setCurrentIndex(index_loc_trailer_subs)

            index_tc_format_loc_trailer = self.tc_format_loc_trailer.findText("23.98fps", QtCore.Qt.MatchFixedString)
            self.tc_format_loc_trailer.setCurrentIndex(index_tc_format_loc_trailer)

            self.loc_trailer_still_tc.setText("")
            self.loc_trailer_top_crop.setText("")
            self.loc_trailer_bottom_crop.setText("")
            self.loc_trailer_left_crop.setText("")
            self.loc_trailer_right_crop.setText("")

            self.loc_trailer_md5_lbl.setText("")

            self.loc_trailer_narr.setChecked(False)
            self.loc_trailer_subs.setChecked(False)

            # trailer assets
            self.loc_trailer_asset1_role.clear()
            self.loc_trailer_asset1_role.addItems(settings.data_roles)

            index_loc_trailer_asset1_locale = self.loc_trailer_asset1_locale.findText("en-US: English (United States)",
                                                                              QtCore.Qt.MatchFixedString)
            self.loc_trailer_asset1_locale.setCurrentIndex(index_loc_trailer_asset1_locale)

            self.loc_trailer_asset2_role.clear()
            self.loc_trailer_asset2_role.addItems(settings.data_roles)

            index_loc_trailer_asset2_locale = self.loc_trailer_asset2_locale.findText("en-US: English (United States)",
                                                                              QtCore.Qt.MatchFixedString)
            self.loc_trailer_asset2_locale.setCurrentIndex(index_loc_trailer_asset2_locale)

            self.loc_trailer_asset3_role.clear()
            self.loc_trailer_asset3_role.addItems(settings.data_roles)

            index_loc_trailer_asset3_locale = self.loc_trailer_asset3_locale.findText("en-US: English (United States)",
                                                                              QtCore.Qt.MatchFixedString)
            self.loc_trailer_asset3_locale.setCurrentIndex(index_loc_trailer_asset3_locale)

            self.loc_trailer_asset4_role.clear()
            self.loc_trailer_asset4_role.addItems(settings.data_roles)

            index_loc_trailer_asset4_locale = self.loc_trailer_asset4_locale.findText("en-US: English (United States)",
                                                                              QtCore.Qt.MatchFixedString)
            self.loc_trailer_asset4_locale.setCurrentIndex(index_loc_trailer_asset4_locale)

            self.loc_trailer_asset5_role.clear()
            self.loc_trailer_asset5_role.addItems(settings.data_roles)

            index_loc_trailer_asset5_locale = self.loc_trailer_asset5_locale.findText("en-US: English (United States)",
                                                                              QtCore.Qt.MatchFixedString)
            self.loc_trailer_asset5_locale.setCurrentIndex(index_loc_trailer_asset5_locale)

            self.loc_trailer_asset6_role.clear()
            self.loc_trailer_asset6_role.addItems(settings.data_roles)

            index_loc_trailer_asset6_locale = self.loc_trailer_asset6_locale.findText("en-US: English (United States)",
                                                                              QtCore.Qt.MatchFixedString)
            self.loc_trailer_asset6_locale.setCurrentIndex(index_loc_trailer_asset6_locale)

            self.loc_trailer_asset7_role.clear()
            self.loc_trailer_asset7_role.addItems(settings.data_roles)

            index_loc_trailer_asset7_locale = self.loc_trailer_asset7_locale.findText("en-US: English (United States)",
                                                                              QtCore.Qt.MatchFixedString)
            self.loc_trailer_asset7_locale.setCurrentIndex(index_loc_trailer_asset7_locale)

            self.loc_trailer_asset8_role.clear()
            self.loc_trailer_asset8_role.addItems(settings.data_roles)

            index_loc_trailer_asset8_locale = self.loc_trailer_asset8_locale.findText("en-US: English (United States)",
                                                                              QtCore.Qt.MatchFixedString)
            self.loc_trailer_asset8_locale.setCurrentIndex(index_loc_trailer_asset8_locale)

            while self.loc_trailer_terr_lyt.count() > 1:
                self.del_territory()

            # process
            index_provider = self.comboProvider.findText("Entertainment One US LP: KochDistribution",
                                                         QtCore.Qt.MatchFixedString)
            self.comboProvider.setCurrentIndex(index_provider)

            index_meta_language = self.comboMetaLanguage.findText("en-US: English (United States)", QtCore.Qt.MatchFixedString)
            self.comboMetaLanguage.setCurrentIndex(index_meta_language)

            self.vendor_id.setText("")

            self.build_scenario.clear()
            self.build_scenario.addItems(settings.scenarios)

            self.build_meta.setCheckState(QtCore.Qt.Unchecked)
            self.build_genres_ratings.setCheckState(QtCore.Qt.Unchecked)
            self.build_cast_crew.setCheckState(QtCore.Qt.Unchecked)
            self.build_feat.setCheckState(QtCore.Qt.Unchecked)
            self.build_feat_assets.setCheckState(QtCore.Qt.Unchecked)
            self.build_chapters.setCheckState(QtCore.Qt.Unchecked)
            self.build_trailer.setCheckState(QtCore.Qt.Unchecked)
            self.build_trailer_assets.setCheckState(QtCore.Qt.Unchecked)
            self.build_poster.setCheckState(QtCore.Qt.Unchecked)
            self.build_product.setCheckState(QtCore.Qt.Unchecked)
            self.build_loc_trailer.setCheckState(QtCore.Qt.Unchecked)
            self.build_loc_trailer_assets.setCheckState(QtCore.Qt.Unchecked)

            # files
            settings.feature_file_path = ""
            settings.feature_file = ""
            settings.trailer_file_path = ""
            settings.trailer_file = ""
            settings.feat_asset1_path = ""
            settings.feat_asset2_path = ""
            settings.feat_asset3_path = ""
            settings.feat_asset4_path = ""
            settings.feat_asset5_path = ""
            settings.feat_asset6_path = ""
            settings.feat_asset7_path = ""
            settings.feat_asset8_path = ""
            settings.trailer_asset1_path = ""
            settings.trailer_asset2_path = ""
            settings.trailer_asset3_path = ""
            settings.trailer_asset4_path = ""
            settings.trailer_asset5_path = ""
            settings.trailer_asset6_path = ""
            settings.trailer_asset7_path = ""
            settings.trailer_asset8_path = ""
            settings.poster_file_path = ""
            settings.loc_trailer_file_path = ""
            settings.loc_trailer_file = ""
            settings.loc_trailer_asset1_path = ""
            settings.loc_trailer_asset2_path = ""
            settings.loc_trailer_asset3_path = ""
            settings.loc_trailer_asset4_path = ""
            settings.loc_trailer_asset5_path = ""
            settings.loc_trailer_asset6_path = ""
            settings.loc_trailer_asset7_path = ""
            settings.loc_trailer_asset8_path = ""
            settings.destination = ""

            self.xml_dest_lbl.setText("")
            self.feature_file_lbl.setText("")
            self.feat_asset1_lbl.setText("")
            self.feat_asset2_lbl.setText("")
            self.feat_asset3_lbl.setText("")
            self.feat_asset4_lbl.setText("")
            self.feat_asset5_lbl.setText("")
            self.feat_asset6_lbl.setText("")
            self.feat_asset7_lbl.setText("")
            self.feat_asset8_lbl.setText("")
            self.trailer_file_lbl.setText("")
            self.trailer_asset1_lbl.setText("")
            self.trailer_asset2_lbl.setText("")
            self.trailer_asset3_lbl.setText("")
            self.trailer_asset4_lbl.setText("")
            self.trailer_asset5_lbl.setText("")
            self.trailer_asset6_lbl.setText("")
            self.trailer_asset7_lbl.setText("")
            self.trailer_asset8_lbl.setText("")
            self.loc_trailer_file_lbl.setText("")
            self.loc_trailer_asset1_lbl.setText("")
            self.loc_trailer_asset2_lbl.setText("")
            self.loc_trailer_asset3_lbl.setText("")
            self.loc_trailer_asset4_lbl.setText("")
            self.loc_trailer_asset5_lbl.setText("")
            self.loc_trailer_asset6_lbl.setText("")
            self.loc_trailer_asset7_lbl.setText("")
            self.loc_trailer_asset8_lbl.setText("")
            self.poster_file_lbl.setText("")


def main():
    app = QtGui.QApplication(sys.argv)
    gui = XmlGeneratorApp()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
