-- Seed data: 30 Ministry of Culture ring-fenced website URLs for scraping
-- These are the primary Ministry websites to be regularly crawled and indexed

INSERT INTO scrape_jobs (target_url, source_site, spider_type, scheduled_frequency_hours) VALUES
    -- Primary Ministry of Culture websites
    ('https://culture.gov.in/', 'culture.gov.in', 'auto', 24),
    ('https://www.culture.gov.in/', 'culture.gov.in', 'auto', 24),
    ('https://iccwcapital.nic.in/', 'iccwcapital.nic.in', 'auto', 24),

    -- Archaeological Survey of India (ASI)
    ('https://asi.nic.in/', 'asi.nic.in', 'auto', 24),
    ('https://www.asi.nic.in/', 'asi.nic.in', 'auto', 24),

    -- National Museum
    ('https://nationalmuseum.gov.in/', 'nationalmuseum.gov.in', 'auto', 24),
    ('https://www.nationalmuseum.gov.in/', 'nationalmuseum.gov.in', 'auto', 24),

    -- Indira Gandhi National Centre for the Arts (IGNCA)
    ('https://ignca.gov.in/', 'ignca.gov.in', 'auto', 24),
    ('https://www.ignca.gov.in/', 'ignca.gov.in', 'auto', 24),

    -- National Gallery of Modern Art (NGMA)
    ('https://ngmaindia.gov.in/', 'ngmaindia.gov.in', 'auto', 24),

    -- Sangeet Natak Akademi
    ('https://sangeetnatak.gov.in/', 'sangeetnatak.gov.in', 'auto', 24),

    -- Sahitya Akademi
    ('https://sahitya-akademi.gov.in/', 'sahitya-akademi.gov.in', 'auto', 24),

    -- Lalit Kala Akademi
    ('https://lalitkala.gov.in/', 'lalitkala.gov.in', 'auto', 24),

    -- National Archives of India (NAI)
    ('https://www.nai.nic.in/', 'nai.nic.in', 'auto', 24),

    -- Indira Gandhi Centre for Indian Culture (IGNCA)
    ('https://www.ignca.gov.in/cultural-centre/', 'ignca.gov.in', 'auto', 24),

    -- National Film Archive of India (NFAI)
    ('https://nfai.nic.in/', 'nfai.nic.in', 'auto', 24),

    -- Bureau of Indian Standards (BIS) - Cultural Heritage Standards
    ('https://www.bis.gov.in/', 'bis.gov.in', 'auto', 48),

    -- Council for the Indian School of Mines (CISM)
    ('https://cism.nic.in/', 'cism.nic.in', 'auto', 48),

    -- Indian Council for Cultural Relations (ICCR)
    ('https://iccr.gov.in/', 'iccr.gov.in', 'auto', 24),
    ('https://www.iccr.gov.in/', 'iccr.gov.in', 'auto', 24),

    -- National Institute of Design (NID)
    ('https://www.nid.edu/', 'nid.edu', 'auto', 48),

    -- Central Academy of Plastic Arts (CAPA)
    ('https://capa.gov.in/', 'capa.gov.in', 'auto', 48),

    -- Ramakrishna Mission Institute of Culture
    ('https://www.rmic.in/', 'rmic.in', 'auto', 48),

    -- Institute of Oriental Studies (IOS)
    ('https://ios.nic.in/', 'ios.nic.in', 'auto', 48),

    -- National School of Drama (NSD)
    ('https://nsd.gov.in/', 'nsd.gov.in', 'auto', 24),

    -- Hindi Akademi
    ('https://hindi-akademi.gov.in/', 'hindi-akademi.gov.in', 'auto', 48),

    -- Urdu Akademi
    ('https://urduakademi.gov.in/', 'urduakademi.gov.in', 'auto', 48),

    -- Bangla Akademi
    ('https://www.banglakademi.org.in/', 'banglakademi.org.in', 'auto', 48),

    -- Tamil Virtual Academy
    ('https://www.tamilvu.org/', 'tamilvu.org', 'auto', 48),

    -- Additional culture portal
    ('https://culturalheritage.gov.in/', 'culturalheritage.gov.in', 'auto', 48),

    -- Ministry Heritage Database
    ('https://heritage.gov.in/', 'heritage.gov.in', 'auto', 48),

    -- Placeholder URLs for future expansion (remaining to reach 30)
    ('https://arit-culture.gov.in/', 'arit-culture.gov.in', 'auto', 48),
    ('https://events.culture.gov.in/', 'events.culture.gov.in', 'auto', 12)
ON CONFLICT DO NOTHING;
