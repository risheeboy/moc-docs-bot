"""Hindi stopword list for NLP preprocessing."""

# Common Hindi stopwords that can be filtered from text
# during tokenization or analysis
HINDI_STOPWORDS = {
    # Articles and demonstratives
    "है",  # is
    "हैं",  # are
    "हो",  # be
    "होना",  # to be
    "होने",  # being
    "था",  # was
    "थे",  # were
    "थी",  # was (feminine)
    "यह",  # this
    "यही",  # this only
    "यहाँ",  # here
    "वह",  # that
    "वही",  # that only
    "वहाँ",  # there
    "कौन",  # who
    "क्या",  # what
    "कहाँ",  # where
    "कब",  # when
    "कैसे",  # how

    # Prepositions
    "में",  # in
    "से",  # from
    "का",  # of/possessive
    "की",  # of/possessive
    "को",  # to/object marker
    "पर",  # on
    "के",  # of/possessive
    "लिए",  # for
    "द्वारा",  # by
    "तक",  # until
    "हेतु",  # for
    "बिना",  # without
    "निकट",  # near

    # Conjunctions
    "और",  # and
    "या",  # or
    "लेकिन",  # but
    "परंतु",  # but
    "किंतु",  # but
    "अगर",  # if
    "जब",  # when
    "तो",  # then
    "यदि",  # if

    # Pronouns
    "मैं",  # I
    "मुझे",  # me
    "तुम",  # you
    "तुम्हें",  # you (object)
    "आप",  # you (formal)
    "हम",  # we
    "हमें",  # us
    "हमारा",  # our
    "मेरा",  # my
    "तुम्हारा",  # your
    "उसका",  # his/her
    "इसका",  # its

    # Common verbs
    "करना",  # do
    "करते",  # doing
    "करेंगे",  # will do
    "किया",  # did
    "कर",  # do
    "रहना",  # stay
    "रहे",  # staying
    "आना",  # come
    "आते",  # coming
    "जाना",  # go
    "जाते",  # going
    "देना",  # give
    "लेना",  # take
    "सकना",  # can
    "चाहना",  # want

    # Articles and quantifiers
    "एक",  # one
    "कुछ",  # some
    "सभी",  # all
    "हर",  # every
    "कोई",  # any

    # Common adverbs
    "भी",  # also
    "ही",  # only
    "तो",  # then
    "न",  # no
    "नहीं",  # no/not
    "नहीं",  # not
    "अब",  # now
    "पहले",  # before
    "बाद",  # after
    "आज",  # today
    "कल",  # tomorrow/yesterday

    # Other common words
    "इस",  # this
    "उस",  # that
    "इन",  # these
    "उन",  # those
    "ये",  # these
    "वे",  # those
    "होगा",  # will be
    "होगी",  # will be (feminine)
    "होंगे",  # will be (plural)
    "है",  # is
    "हैं",  # are
    "हो",  # are
    "हूं",  # am
    "हूँ",  # am
}


def is_hindi_stopword(word: str) -> bool:
    """Check if word is a Hindi stopword.

    Args:
        word: Word to check

    Returns:
        True if word is a stopword
    """
    return word.lower() in HINDI_STOPWORDS


def filter_stopwords(words: list[str]) -> list[str]:
    """Filter out Hindi stopwords from word list.

    Args:
        words: List of words

    Returns:
        List with stopwords removed
    """
    return [w for w in words if w.lower() not in HINDI_STOPWORDS]
