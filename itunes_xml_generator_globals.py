#!/usr/bin/python
# -*- coding: utf-8 -*-

# iTunes Xml Generator Globals
#
# Author: Simon Lachaîne


from collections import OrderedDict

directory = ""
relaxng_doc = ""

# metadata
vendor = ""
country = ""
spoken = ""
title = ""
studio_title = ""
synopsis = ""
company = ""
cline = ""
theatrical = ""

# genres and ratings
genre1 = ""
genre2 = ""
genre3 = ""
genre4 = ""
genre5 = ""
genre6 = ""
genre7 = ""
genre8 = ""

rating1_sys = ""
rating2_sys = ""
rating3_sys = ""
rating4_sys = ""
rating5_sys = ""

rating1_value = ""
rating2_value = ""
rating3_value = ""
rating4_value = ""
rating5_value = ""

# cast and crew
actor1_name = ""
actor2_name = ""
actor3_name = ""
actor4_name = ""
actor5_name = ""
actor6_name = ""
actor7_name = ""
actor8_name = ""
actor9_name = ""
actor10_name = ""

actor1_apple_id = ""
actor2_apple_id = ""
actor3_apple_id = ""
actor4_apple_id = ""
actor5_apple_id = ""
actor6_apple_id = ""
actor7_apple_id = ""
actor8_apple_id = ""
actor9_apple_id = ""
actor10_apple_id = ""

actor1_char = ""
actor2_char = ""
actor3_char = ""
actor4_char = ""
actor5_char = ""
actor6_char = ""
actor7_char = ""
actor8_char = ""
actor9_char = ""
actor10_char = ""

actor1_char2 = ""
actor2_char2 = ""
actor3_char2 = ""
actor4_char2 = ""
actor5_char2 = ""
actor6_char2 = ""
actor7_char2 = ""
actor8_char2 = ""
actor9_char2 = ""
actor10_char2 = ""

actor1_ref = ""
actor2_ref = ""
actor3_ref = ""
actor4_ref = ""
actor5_ref = ""
actor6_ref = ""
actor7_ref = ""
actor8_ref = ""
actor9_ref = ""
actor10_ref = ""

actor1_ref2 = ""
actor2_ref2 = ""
actor3_ref2 = ""
actor4_ref2 = ""
actor5_ref2 = ""
actor6_ref2 = ""
actor7_ref2 = ""
actor8_ref2 = ""
actor9_ref2 = ""
actor10_ref2 = ""

crew1_name = ""
crew2_name = ""
crew3_name = ""
crew4_name = ""
crew5_name = ""
crew6_name = ""
crew7_name = ""
crew8_name = ""
crew9_name = ""
crew10_name = ""

crew1_apple_id = ""
crew2_apple_id = ""
crew3_apple_id = ""
crew4_apple_id = ""
crew5_apple_id = ""
crew6_apple_id = ""
crew7_apple_id = ""
crew8_apple_id = ""
crew9_apple_id = ""
crew10_apple_id = ""

crew1_director = False
crew1_producer = False
crew1_screenwriter = False
crew1_composer = False
crew1_codirector = False

crew2_director = False
crew2_producer = False
crew2_screenwriter = False
crew2_composer = False
crew2_codirector = False

crew3_director = False
crew3_producer = False
crew3_screenwriter = False
crew3_composer = False
crew3_codirector = False

crew4_director = False
crew4_producer = False
crew4_screenwriter = False
crew4_composer = False
crew4_codirector = False

crew5_director = False
crew5_producer = False
crew5_screenwriter = False
crew5_composer = False
crew5_codirector = False

crew6_director = False
crew6_producer = False
crew6_screenwriter = False
crew6_composer = False
crew6_codirector = False

crew7_director = False
crew7_producer = False
crew7_screenwriter = False
crew7_composer = False
crew7_codirector = False

crew8_director = False
crew8_producer = False
crew8_screenwriter = False
crew8_composer = False
crew8_codirector = False

crew9_director = False
crew9_producer = False
crew9_screenwriter = False
crew9_composer = False
crew9_codirector = False

crew10_director = False
crew10_producer = False
crew10_screenwriter = False
crew10_composer = False
crew10_codirector = False

# feature
feature_file_path = ""
feature_file = ""
feature_md5 = ""
feature_audio = ""
narr_feat = ""
sub_feat = ""
feat_crop_top = ""
feat_crop_bottom = ""
feat_crop_left = ""
feat_crop_right = ""

# chapters
tc_format = "23.98fps"
pack_info_path = ""
chapters_tc = OrderedDict()
thumbs_tc = OrderedDict()
chapter_locales = OrderedDict()
chapters_done = True

# trailer
trailer_file_path = ""
trailer_file = ""
trailer_md5 = ""
trailer_still = ""
trailer_tc = "23.98fps"
trailer_audio = ""
narr_trailer = ""
sub_trailer = ""
trailer_crop_top = ""
trailer_crop_bottom = ""
trailer_crop_left = ""
trailer_crop_right = ""

# feature assets
feat_asset1_role = "notes"
feat_asset2_role = "notes"
feat_asset3_role = "notes"
feat_asset4_role = "notes"
feat_asset5_role = "notes"
feat_asset6_role = "notes"
feat_asset7_role = "notes"
feat_asset8_role = "notes"
feat_asset1_locale = ""
feat_asset2_locale = ""
feat_asset3_locale = ""
feat_asset4_locale = ""
feat_asset5_locale = ""
feat_asset6_locale = ""
feat_asset7_locale = ""
feat_asset8_locale = ""
feat_asset1_path = ""
feat_asset2_path = ""
feat_asset3_path = ""
feat_asset4_path = ""
feat_asset5_path = ""
feat_asset6_path = ""
feat_asset7_path = ""
feat_asset8_path = ""
feat_asset1_territories = OrderedDict()
feat_asset2_territories = OrderedDict()
feat_asset3_territories = OrderedDict()
feat_asset4_territories = OrderedDict()
feat_asset5_territories = OrderedDict()
feat_asset6_territories = OrderedDict()
feat_asset7_territories = OrderedDict()
feat_asset8_territories = OrderedDict()

# trailer assets
trailer_asset1_role = "notes"
trailer_asset2_role = "notes"
trailer_asset3_role = "notes"
trailer_asset4_role = "notes"
trailer_asset5_role = "notes"
trailer_asset6_role = "notes"
trailer_asset7_role = "notes"
trailer_asset8_role = "notes"
trailer_asset1_locale = ""
trailer_asset2_locale = ""
trailer_asset3_locale = ""
trailer_asset4_locale = ""
trailer_asset5_locale = ""
trailer_asset6_locale = ""
trailer_asset7_locale = ""
trailer_asset8_locale = ""
trailer_asset1_path = ""
trailer_asset2_path = ""
trailer_asset3_path = ""
trailer_asset4_path = ""
trailer_asset5_path = ""
trailer_asset6_path = ""
trailer_asset7_path = ""
trailer_asset8_path = ""

# poster art
poster_locale = ""
poster_file_path = ""

# products
product1_check = False
product1_sales_start_check = True
product1_sales_end_check = True
product1_preorder_check = True
product1_vod_start_check = True
product1_vod_end_check = True
product1_physical_check = True
product1_price_sd_check = True
product1_price_hd_check = True
product1_vod_type_check = True
product1_terr = ""
product1_sale_clear = "true"
product1_price_sd = ""
product1_price_hd = ""
product1_sales_start = ""
product1_sales_end = ""
product1_preorder = ""
product1_vod_clear = "true"
product1_vod_type = "New Release"
product1_vod_start = ""
product1_vod_end = ""
product1_physical = ""

product2_check = False
product2_sales_start_check = True
product2_sales_end_check = True
product2_preorder_check = True
product2_vod_start_check = True
product2_vod_end_check = True
product2_physical_check = True
product2_price_sd_check = True
product2_price_hd_check = True
product2_vod_type_check = True
product2_terr = ""
product2_sale_clear = "true"
product2_price_sd = ""
product2_price_hd = ""
product2_sales_start = ""
product2_sales_end = ""
product2_preorder = ""
product2_vod_clear = "true"
product2_vod_type = "New Release"
product2_vod_start = ""
product2_vod_end = ""
product2_physical = ""

product3_check = False
product3_sales_start_check = True
product3_sales_end_check = True
product3_preorder_check = True
product3_vod_start_check = True
product3_vod_end_check = True
product3_physical_check = True
product3_price_sd_check = True
product3_price_hd_check = True
product3_vod_type_check = True
product3_terr = ""
product3_sale_clear = "true"
product3_price_sd = ""
product3_price_hd = ""
product3_sales_start = ""
product3_sales_end = ""
product3_preorder = ""
product3_vod_clear = "true"
product3_vod_type = "New Release"
product3_vod_start = ""
product3_vod_end = ""
product3_physical = ""

product4_check = False
product4_sales_start_check = True
product4_sales_end_check = True
product4_preorder_check = True
product4_vod_start_check = True
product4_vod_end_check = True
product4_physical_check = True
product4_price_sd_check = True
product4_price_hd_check = True
product4_vod_type_check = True
product4_terr = ""
product4_sale_clear = "true"
product4_price_sd = ""
product4_price_hd = ""
product4_sales_start = ""
product4_sales_end = ""
product4_preorder = ""
product4_vod_clear = "true"
product4_vod_type = "New Release"
product4_vod_start = ""
product4_vod_end = ""
product4_physical = ""

# localization
localized_check_1 = False
localized_locale_1 = ""
localized_title_1 = ""
localized_synopsis_1 = ""

localized_check_2 = False
localized_locale_2 = ""
localized_title_2 = ""
localized_synopsis_2 = ""

localized_check_3 = False
localized_locale_3 = ""
localized_title_3 = ""
localized_synopsis_3 = ""

localized_check_4 = False
localized_locale_4 = ""
localized_title_4 = ""
localized_synopsis_4 = ""

# localized trailer
loc_trailer_file_path = ""
loc_trailer_file = ""
loc_trailer_md5 = ""
loc_trailer_still = ""
loc_trailer_tc = "23.98fps"
loc_trailer_audio = ""
narr_loc_trailer = ""
sub_loc_trailer = ""
loc_trailer_crop_top = ""
loc_trailer_crop_bottom = ""
loc_trailer_crop_left = ""
loc_trailer_crop_right = ""
loc_trailer_territories = OrderedDict()

# localized trailer assets
loc_trailer_asset1_role = "notes"
loc_trailer_asset2_role = "notes"
loc_trailer_asset3_role = "notes"
loc_trailer_asset4_role = "notes"
loc_trailer_asset5_role = "notes"
loc_trailer_asset6_role = "notes"
loc_trailer_asset7_role = "notes"
loc_trailer_asset8_role = "notes"
loc_trailer_asset1_locale = ""
loc_trailer_asset2_locale = ""
loc_trailer_asset3_locale = ""
loc_trailer_asset4_locale = ""
loc_trailer_asset5_locale = ""
loc_trailer_asset6_locale = ""
loc_trailer_asset7_locale = ""
loc_trailer_asset8_locale = ""
loc_trailer_asset1_path = ""
loc_trailer_asset2_path = ""
loc_trailer_asset3_path = ""
loc_trailer_asset4_path = ""
loc_trailer_asset5_path = ""
loc_trailer_asset6_path = ""
loc_trailer_asset7_path = ""
loc_trailer_asset8_path = ""

# process
provider = ""
language_meta = ""
destination = ""
results = ""

# flags
providers_txt_missing = False
feat_check_narr = False
feat_check_subs = False
trailer_check_narr = False
trailer_check_subs = False
loc_trailer_check_narr = False
loc_trailer_check_subs = False
meta = False
genres_ratings = False
cast_crew = False
feature = False
feature_assets = False
chapters = False
trailer = False
trailer_assets = False
loc_trailer = False
loc_trailer_assets = False
poster = False
product = False

# lists and dictionaries
countries = {}
providers_lst = []
cleared_choices = [
    "true",
    "false"
]
vod_types = [
    "New Release",
    "Library"
]
data_roles = [
    "notes",
    "captions",
    "subtitles",
    "forced_subtitles",
    "subtitles.hearing_impaired",
    "audio",
    "audio.7_1",
    "audio.visually_impaired",
    "video.end.dub_credits"
]
timecodes = {
    "24fps": "24/1 1/nonDrop",
    "23.98fps": "24/999 1000/nonDrop",
    "25fps": "25/1 1/nonDrop",
    "30fps drop": "30/999 1000/dropNTSC",
    "30fps non-drop": "30/999 1000/nonDrop"
}
scenarios = [
    "",
    "Full Package",
    "Asset Update",
    "Assetless preorder"
]