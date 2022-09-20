# -*- coding: utf-8 -*-
#
# Set up arrays and data dictionaries for use with several functions
#

batchmonth = list(range(1, 13))
batchoptions = list(range(1, 11))

menudata = {
    1: {
        "description": "Monthly Temperature Range",
        "heading": "TEMP_RANGE",
        "title": "Monthly Temperature Range",
    },
    2: {
        "description": "Mean Temperature",
        "heading": "MEAN_TEMP",
        "title": "Mean Temp",
    },
    3: {
        "description": "High Temperature",
        "heading": "HIGH_TEMP",
        "title": "High Temp",
    },
    4: {
        "description": "Low Temperature",
        "heading": "LOW_TEMP",
        "title": "Low Temp",
    },
    5: {
        "description": "Sum Of Heating degree days",
        "heading": "HEAT_DEG_DAYS",
        "title": "Sum of Heating Degree Days",
    },
    6: {
        "description": "Sum Of Cooling degree days",
        "heading": "COOL_DEG_DAYS",
        "title": "Sum of Cooling Degree Days",
    },
    7: {
        "description": "Precipitation",
        "heading": "PRECIPITATION",
        "title": "Precipitation Total",
    },
    8: {
        "description": "Average Wind Speed",
        "heading": "AVG_WIND_SPEED",
        "title": "Average Wind Speed",
    },
    9: {
        "description": "High Wind Gust",
        "heading": "HIGH_WIND_GUST",
        "title": "High Wind Gust",
    },
    10: {
        "description": "Dominant Wind Direction",
        "heading": "DOMINANT_WIND_DIRECTION",
        "title": "Dominant Wind Direction",
    },

    11: {
        "description": "Switch to another month",
        "heading": "N/A",
        "title": "N/A",
    },
    12: {
        "description": "Exit",
        "heading": "N/A",
        "title": "N/A",
    },
}

headings = [
    "DAY",
    "MEAN_TEMP",
    "HIGH_TEMP",
    "TIME_HIGH_TEMP",
    "LOW_TEMP",
    "TIME_LOW_TEMP",
    "HEAT_DEG_DAYS",
    "COOL_DEG_DAYS",
    "PRECIPITATION",
    "AVG_WIND_SPEED",
    "HIGH_WIND_GUST",
    "TIME_WIND_GUST",
    "DOMINANT_WIND_DIRECTION",
]

# Have to hardcode where the columns begin and end. This template helps:
#
#       MEAN                               DEG    DEG          WIND                   DOM
# DAY   TEMP   HIGH   TIME    LOW   TIME   DAYS   DAYS   RAIN  SPEED   HIGH   TIME    DIR
# 0         1         2         3         4         5         6         7         8
# 012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789
# ---------------------------------------------------------------------------------------
# DAY   TEMP   HIGH   TIME    LOW   TIME   DAYS   DAYS   RAIN  SPEED   HIGH   TIME    DIR
# ---------------------------------------------------------------------------------------

colspecs = [
    (0, 3),
    (5, 10),
    (13, 17),
    (18, 24),
    (25, 31),
    (33, 38),
    (39, 45),
    (46, 52),
    (53, 60),
    (60, 66),
    (67, 73),
    (75, 80),
    (84, 87),
]

# US(1), METRICWX(2), or METRIC(3).
# The difference between METRICWX, and METRIC is that
# the former uses mm instead of cm for rain, and m/s
# instead of km/hr for wind speed.

unitdata = {
    'US': {
        "temp": "°F",
        "precip": "in",
        "speed": "mph",
    },
    'METRICWX': {
        "temp": "°C",
        "precip": "mm",
        "speed": "m/s",
    },
    'METRIC': {
        "temp": "°C",
        "precip": "cm",
        "speed": "km/h",
    },

}
