--
-- PostgreSQL database dump
--

-- Started on 2011-04-21 17:27:12 EDT

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = off;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET escape_string_warning = off;

--
-- TOC entry 9 (class 2615 OID 16865)
-- Name: taxa; Type: SCHEMA; Schema: -; Owner: danr
--

CREATE SCHEMA taxa;


ALTER SCHEMA taxa OWNER TO danr;

SET search_path = taxa, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- TOC entry 1534 (class 1259 OID 16907)
-- Dependencies: 9
-- Name: name_source; Type: TABLE; Schema: taxa; Owner: danr; Tablespace: 
--

CREATE TABLE name_source (
    record_id integer NOT NULL,
    source_name character varying(30) NOT NULL,
    source_description character varying(120)
);


ALTER TABLE taxa.name_source OWNER TO danr;

--
-- TOC entry 1830 (class 0 OID 0)
-- Dependencies: 1534
-- Name: TABLE name_source; Type: COMMENT; Schema: taxa; Owner: danr
--

COMMENT ON TABLE name_source IS 'This table stores the source for a name or synonym.  It is expected to list data sources such as a database (eg IUCN Redlist), a phylogeny or a specimen dataset (eg GBIF or a museum), rather than the publication which described a taxon.';


--
-- TOC entry 1533 (class 1259 OID 16905)
-- Dependencies: 1534 9
-- Name: name_source_record_id_seq; Type: SEQUENCE; Schema: taxa; Owner: danr
--

CREATE SEQUENCE name_source_record_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE taxa.name_source_record_id_seq OWNER TO danr;

--
-- TOC entry 1832 (class 0 OID 0)
-- Dependencies: 1533
-- Name: name_source_record_id_seq; Type: SEQUENCE OWNED BY; Schema: taxa; Owner: danr
--

ALTER SEQUENCE name_source_record_id_seq OWNED BY name_source.record_id;


--
-- TOC entry 1532 (class 1259 OID 16894)
-- Dependencies: 1819 9
-- Name: synonyms; Type: TABLE; Schema: taxa; Owner: mol; Tablespace: 
--

CREATE TABLE synonyms (
    record_id integer NOT NULL,
    lsid character varying(83),
    name character varying(137) NOT NULL,
    taxon character varying(12) NOT NULL,
    name_code character varying(42),
    parent_id integer NOT NULL,
    is_accepted_name smallint NOT NULL,
    is_species_or_nonsynonymic_higher_taxon smallint NOT NULL,
    accepted_name_code character varying(42)[],
    accepted_name character varying(137),
    name_source_id integer DEFAULT 1 NOT NULL
);


ALTER TABLE taxa.synonyms OWNER TO mol;

--
-- TOC entry 1833 (class 0 OID 0)
-- Dependencies: 1532
-- Name: TABLE synonyms; Type: COMMENT; Schema: taxa; Owner: mol
--

COMMENT ON TABLE synonyms IS 'This table stores synonyms to col taxa, in addition to those found in col.scientific_names';


--
-- TOC entry 1531 (class 1259 OID 16892)
-- Dependencies: 9 1532
-- Name: synonyms_record_id_seq; Type: SEQUENCE; Schema: taxa; Owner: mol
--

CREATE SEQUENCE synonyms_record_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE taxa.synonyms_record_id_seq OWNER TO mol;

--
-- TOC entry 1834 (class 0 OID 0)
-- Dependencies: 1531
-- Name: synonyms_record_id_seq; Type: SEQUENCE OWNED BY; Schema: taxa; Owner: mol
--

ALTER SEQUENCE synonyms_record_id_seq OWNED BY synonyms.record_id;


--
-- TOC entry 1820 (class 2604 OID 16910)
-- Dependencies: 1533 1534 1534
-- Name: record_id; Type: DEFAULT; Schema: taxa; Owner: danr
--

ALTER TABLE name_source ALTER COLUMN record_id SET DEFAULT nextval('name_source_record_id_seq'::regclass);


--
-- TOC entry 1818 (class 2604 OID 16897)
-- Dependencies: 1531 1532 1532
-- Name: record_id; Type: DEFAULT; Schema: taxa; Owner: mol
--

ALTER TABLE synonyms ALTER COLUMN record_id SET DEFAULT nextval('synonyms_record_id_seq'::regclass);


--
-- TOC entry 1825 (class 2606 OID 16912)
-- Dependencies: 1534 1534
-- Name: name_source_pkey; Type: CONSTRAINT; Schema: taxa; Owner: danr; Tablespace: 
--

ALTER TABLE ONLY name_source
    ADD CONSTRAINT name_source_pkey PRIMARY KEY (record_id);


--
-- TOC entry 1823 (class 2606 OID 16903)
-- Dependencies: 1532 1532
-- Name: synonyms_pkey; Type: CONSTRAINT; Schema: taxa; Owner: mol; Tablespace: 
--

ALTER TABLE ONLY synonyms
    ADD CONSTRAINT synonyms_pkey PRIMARY KEY (record_id);


--
-- TOC entry 1821 (class 1259 OID 16901)
-- Dependencies: 1532
-- Name: synonyms_name_idx; Type: INDEX; Schema: taxa; Owner: mol; Tablespace: 
--

CREATE INDEX synonyms_name_idx ON synonyms USING btree (name);


--
-- TOC entry 1826 (class 2606 OID 16922)
-- Dependencies: 1824 1534 1532
-- Name: name_source_fkey; Type: FK CONSTRAINT; Schema: taxa; Owner: mol
--

ALTER TABLE ONLY synonyms
    ADD CONSTRAINT name_source_fkey FOREIGN KEY (name_source_id) REFERENCES name_source(record_id);


--
-- TOC entry 1829 (class 0 OID 0)
-- Dependencies: 9
-- Name: taxa; Type: ACL; Schema: -; Owner: danr
--

REVOKE ALL ON SCHEMA taxa FROM PUBLIC;
REVOKE ALL ON SCHEMA taxa FROM danr;
GRANT ALL ON SCHEMA taxa TO danr;
GRANT ALL ON SCHEMA taxa TO mol;


--
-- TOC entry 1831 (class 0 OID 0)
-- Dependencies: 1534
-- Name: name_source; Type: ACL; Schema: taxa; Owner: danr
--

REVOKE ALL ON TABLE name_source FROM PUBLIC;
REVOKE ALL ON TABLE name_source FROM danr;
GRANT ALL ON TABLE name_source TO danr;
GRANT SELECT ON TABLE name_source TO mol_query;
GRANT ALL ON TABLE name_source TO mol_user;


-- Completed on 2011-04-21 17:27:13 EDT

--
-- PostgreSQL database dump complete
--

