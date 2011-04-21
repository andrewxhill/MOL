--
-- PostgreSQL database dump
--

-- Started on 2011-04-21 16:28:33 EDT

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = off;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET escape_string_warning = off;

--
-- TOC entry 8 (class 2615 OID 16390)
-- Name: mol; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA mol;


ALTER SCHEMA mol OWNER TO postgres;

SET search_path = mol, pg_catalog;

SET default_tablespace = mol_tablespace;

SET default_with_oids = false;

--
-- TOC entry 1529 (class 1259 OID 16831)
-- Dependencies: 8
-- Name: analysis_register; Type: TABLE; Schema: mol; Owner: mol; Tablespace: mol_tablespace
--

CREATE TABLE analysis_register (
    taxonid numeric(11,0) NOT NULL,
    taxonname character varying(50),
    taxoncommonname character varying(115),
    taxonlevelid numeric(3,0),
    themeid smallint NOT NULL,
    pucount numeric(5,0),
    putype character varying(1) NOT NULL,
    datedone timestamp with time zone
);


ALTER TABLE mol.analysis_register OWNER TO mol;

--
-- TOC entry 1836 (class 0 OID 0)
-- Dependencies: 1529
-- Name: COLUMN analysis_register.taxonid; Type: COMMENT; Schema: mol; Owner: mol
--

COMMENT ON COLUMN analysis_register.taxonid IS 'Taxon ID for the parent taxon of the analysis (eg 14890 for Gekkonidae family)';


--
-- TOC entry 1837 (class 0 OID 0)
-- Dependencies: 1529
-- Name: COLUMN analysis_register.taxonname; Type: COMMENT; Schema: mol; Owner: mol
--

COMMENT ON COLUMN analysis_register.taxonname IS 'Scientific name of parent taxon (eg Gekkonidae) - optional field - could leave out and add this info by query when needed.';


--
-- TOC entry 1838 (class 0 OID 0)
-- Dependencies: 1529
-- Name: COLUMN analysis_register.taxoncommonname; Type: COMMENT; Schema: mol; Owner: mol
--

COMMENT ON COLUMN analysis_register.taxoncommonname IS 'Common name of parent taxon (eg Gekkoes) - optional field - could leave out and add this info by query when needed.';


--
-- TOC entry 1839 (class 0 OID 0)
-- Dependencies: 1529
-- Name: COLUMN analysis_register.taxonlevelid; Type: COMMENT; Schema: mol; Owner: mol
--

COMMENT ON COLUMN analysis_register.taxonlevelid IS 'Taxon level of parent taxon (eg 8 for family) - optional field - could leave out and add this info by query when needed.';


--
-- TOC entry 1840 (class 0 OID 0)
-- Dependencies: 1529
-- Name: COLUMN analysis_register.themeid; Type: COMMENT; Schema: mol; Owner: mol
--

COMMENT ON COLUMN analysis_register.themeid IS 'Identifies the type of analysis (eg 1 for species richness)';


--
-- TOC entry 1841 (class 0 OID 0)
-- Dependencies: 1529
-- Name: COLUMN analysis_register.pucount; Type: COMMENT; Schema: mol; Owner: mol
--

COMMENT ON COLUMN analysis_register.pucount IS 'Number of records (ie planning units in the Scores table for this item)';


--
-- TOC entry 1842 (class 0 OID 0)
-- Dependencies: 1529
-- Name: COLUMN analysis_register.putype; Type: COMMENT; Schema: mol; Owner: mol
--

COMMENT ON COLUMN analysis_register.putype IS 'Type of Planning unit (T)errestrial or (M)arine';


--
-- TOC entry 1843 (class 0 OID 0)
-- Dependencies: 1529
-- Name: COLUMN analysis_register.datedone; Type: COMMENT; Schema: mol; Owner: mol
--

COMMENT ON COLUMN analysis_register.datedone IS 'Date/Time when this analysis was last done for all planning units';


--
-- TOC entry 1536 (class 1259 OID 16983)
-- Dependencies: 8
-- Name: occurrence; Type: TABLE; Schema: mol; Owner: mol; Tablespace: mol_tablespace
--

CREATE TABLE occurrence (
    occurrence_id integer NOT NULL,
    grid_name character varying(25),
    cell_id numeric(10,0) NOT NULL,
    taxon_id numeric(11,0) NOT NULL,
    date_done timestamp with time zone
);


ALTER TABLE mol.occurrence OWNER TO mol;

--
-- TOC entry 1845 (class 0 OID 0)
-- Dependencies: 1536
-- Name: TABLE occurrence; Type: COMMENT; Schema: mol; Owner: mol
--

COMMENT ON TABLE occurrence IS 'Lists taxon occurrence for each cell in one or more grids';


--
-- TOC entry 1846 (class 0 OID 0)
-- Dependencies: 1536
-- Name: COLUMN occurrence.occurrence_id; Type: COMMENT; Schema: mol; Owner: mol
--

COMMENT ON COLUMN occurrence.occurrence_id IS 'unique ID for records in this table.';


--
-- TOC entry 1847 (class 0 OID 0)
-- Dependencies: 1536
-- Name: COLUMN occurrence.grid_name; Type: COMMENT; Schema: mol; Owner: mol
--

COMMENT ON COLUMN occurrence.grid_name IS 'the name of the grid (a spatial layer) which defined the spatial units used for the analysis';


--
-- TOC entry 1848 (class 0 OID 0)
-- Dependencies: 1536
-- Name: COLUMN occurrence.cell_id; Type: COMMENT; Schema: mol; Owner: mol
--

COMMENT ON COLUMN occurrence.cell_id IS 'a grid cell in the grid listed in the gridname field';


--
-- TOC entry 1849 (class 0 OID 0)
-- Dependencies: 1536
-- Name: COLUMN occurrence.taxon_id; Type: COMMENT; Schema: mol; Owner: mol
--

COMMENT ON COLUMN occurrence.taxon_id IS 'Taxon ID for a taxon recorded in a cell';


--
-- TOC entry 1850 (class 0 OID 0)
-- Dependencies: 1536
-- Name: COLUMN occurrence.date_done; Type: COMMENT; Schema: mol; Owner: mol
--

COMMENT ON COLUMN occurrence.date_done IS 'Date/Time when this occurence record was created / updated from species range data';


--
-- TOC entry 1535 (class 1259 OID 16981)
-- Dependencies: 8 1536
-- Name: occurrence_occurrence_id_seq; Type: SEQUENCE; Schema: mol; Owner: mol
--

CREATE SEQUENCE occurrence_occurrence_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE mol.occurrence_occurrence_id_seq OWNER TO mol;

--
-- TOC entry 1851 (class 0 OID 0)
-- Dependencies: 1535
-- Name: occurrence_occurrence_id_seq; Type: SEQUENCE OWNED BY; Schema: mol; Owner: mol
--

ALTER SEQUENCE occurrence_occurrence_id_seq OWNED BY occurrence.occurrence_id;


--
-- TOC entry 1530 (class 1259 OID 16845)
-- Dependencies: 1818 1819 8
-- Name: themes; Type: TABLE; Schema: mol; Owner: mol; Tablespace: mol_tablespace
--

CREATE TABLE themes (
    themeid smallint NOT NULL,
    themename character varying(50),
    themedesc character varying(200),
    alltaxa boolean DEFAULT true,
    implemented boolean DEFAULT false,
    comment text,
    reference text,
    abbreviation character varying(10)
);


ALTER TABLE mol.themes OWNER TO mol;

--
-- TOC entry 1852 (class 0 OID 0)
-- Dependencies: 1530
-- Name: TABLE themes; Type: COMMENT; Schema: mol; Owner: mol
--

COMMENT ON TABLE themes IS 'This table defines the types of analysis which can be performed on groups of taxa in cells';


--
-- TOC entry 1820 (class 2604 OID 16986)
-- Dependencies: 1535 1536 1536
-- Name: occurrence_id; Type: DEFAULT; Schema: mol; Owner: mol
--

ALTER TABLE occurrence ALTER COLUMN occurrence_id SET DEFAULT nextval('occurrence_occurrence_id_seq'::regclass);


--
-- TOC entry 1822 (class 2606 OID 16853)
-- Dependencies: 1529 1529 1529 1529
-- Name: analysis_pkey; Type: CONSTRAINT; Schema: mol; Owner: mol; Tablespace: mol_tablespace
--

ALTER TABLE ONLY analysis_register
    ADD CONSTRAINT analysis_pkey PRIMARY KEY (taxonid, themeid, putype);


--
-- TOC entry 1830 (class 2606 OID 16988)
-- Dependencies: 1536 1536
-- Name: occurrence_pkey; Type: CONSTRAINT; Schema: mol; Owner: mol; Tablespace: mol_tablespace
--

ALTER TABLE ONLY occurrence
    ADD CONSTRAINT occurrence_pkey PRIMARY KEY (occurrence_id);


--
-- TOC entry 1826 (class 2606 OID 16851)
-- Dependencies: 1530 1530
-- Name: themes_pkey; Type: CONSTRAINT; Schema: mol; Owner: mol; Tablespace: mol_tablespace
--

ALTER TABLE ONLY themes
    ADD CONSTRAINT themes_pkey PRIMARY KEY (themeid);


SET default_tablespace = '';

--
-- TOC entry 1827 (class 1259 OID 16990)
-- Dependencies: 1536
-- Name: cell_idx; Type: INDEX; Schema: mol; Owner: mol; Tablespace: 
--

CREATE INDEX cell_idx ON occurrence USING btree (cell_id);


--
-- TOC entry 1823 (class 1259 OID 16859)
-- Dependencies: 1529
-- Name: fki_themes_fkey; Type: INDEX; Schema: mol; Owner: mol; Tablespace: 
--

CREATE INDEX fki_themes_fkey ON analysis_register USING btree (themeid);


SET default_tablespace = mol_tablespace;

--
-- TOC entry 1828 (class 1259 OID 16989)
-- Dependencies: 1536
-- Name: grid_name_idx; Type: INDEX; Schema: mol; Owner: mol; Tablespace: mol_tablespace
--

CREATE INDEX grid_name_idx ON occurrence USING btree (grid_name);


SET default_tablespace = '';

--
-- TOC entry 1831 (class 1259 OID 16991)
-- Dependencies: 1536
-- Name: taxon_occurrence_idx; Type: INDEX; Schema: mol; Owner: mol; Tablespace: 
--

CREATE INDEX taxon_occurrence_idx ON occurrence USING btree (taxon_id);


SET default_tablespace = mol_tablespace;

--
-- TOC entry 1824 (class 1259 OID 16931)
-- Dependencies: 1530
-- Name: themes_idx; Type: INDEX; Schema: mol; Owner: mol; Tablespace: mol_tablespace
--

CREATE UNIQUE INDEX themes_idx ON themes USING btree (themeid NULLS FIRST);


--
-- TOC entry 1832 (class 2606 OID 16854)
-- Dependencies: 1529 1530 1825
-- Name: themes_fkey; Type: FK CONSTRAINT; Schema: mol; Owner: mol
--

ALTER TABLE ONLY analysis_register
    ADD CONSTRAINT themes_fkey FOREIGN KEY (themeid) REFERENCES themes(themeid);


--
-- TOC entry 1835 (class 0 OID 0)
-- Dependencies: 8
-- Name: mol; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA mol FROM PUBLIC;
REVOKE ALL ON SCHEMA mol FROM postgres;
GRANT ALL ON SCHEMA mol TO postgres;
GRANT ALL ON SCHEMA mol TO mol;
GRANT USAGE ON SCHEMA mol TO mol_query;


--
-- TOC entry 1844 (class 0 OID 0)
-- Dependencies: 1529
-- Name: analysis_register; Type: ACL; Schema: mol; Owner: mol
--

REVOKE ALL ON TABLE analysis_register FROM PUBLIC;
REVOKE ALL ON TABLE analysis_register FROM mol;
GRANT ALL ON TABLE analysis_register TO mol;
GRANT SELECT ON TABLE analysis_register TO mol_query;
GRANT SELECT,INSERT,REFERENCES,DELETE,TRUNCATE,UPDATE ON TABLE analysis_register TO mol_user;


--
-- TOC entry 1853 (class 0 OID 0)
-- Dependencies: 1530
-- Name: themes; Type: ACL; Schema: mol; Owner: mol
--

REVOKE ALL ON TABLE themes FROM PUBLIC;
REVOKE ALL ON TABLE themes FROM mol;
GRANT ALL ON TABLE themes TO mol;
GRANT SELECT ON TABLE themes TO mol_query;
GRANT SELECT,INSERT,REFERENCES,DELETE,TRUNCATE,UPDATE ON TABLE themes TO mol_user;


-- Completed on 2011-04-21 16:28:33 EDT

--
-- PostgreSQL database dump complete
--

