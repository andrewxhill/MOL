--
-- PostgreSQL database dump
--

-- Started on 2011-04-21 17:25:44 EDT

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = off;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET escape_string_warning = off;

--
-- TOC entry 7 (class 2615 OID 16391)
-- Name: col; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA col;


ALTER SCHEMA col OWNER TO postgres;

--
-- TOC entry 1874 (class 0 OID 0)
-- Dependencies: 7
-- Name: SCHEMA col; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON SCHEMA col IS 'Catalog of Life taxonomy';


SET search_path = col, pg_catalog;

SET default_tablespace = mol_tablespace;

SET default_with_oids = false;

--
-- TOC entry 1523 (class 1259 OID 16528)
-- Dependencies: 1828 1829 1830 1831 1832 1833 1834 1835 1836 7
-- Name: families; Type: TABLE; Schema: col; Owner: mol; Tablespace: mol_tablespace
--

CREATE TABLE families (
    record_id integer NOT NULL,
    hierarchy_code character varying(250) NOT NULL,
    kingdom character varying(50) DEFAULT ''::character varying NOT NULL,
    phylum character varying(50) DEFAULT ''::character varying NOT NULL,
    class character varying(50) DEFAULT ''::character varying NOT NULL,
    taxonorder character varying(50) DEFAULT ''::character varying NOT NULL,
    family character varying(50) DEFAULT ''::character varying NOT NULL,
    superfamily character varying(50) DEFAULT NULL::character varying,
    family_common_name character varying(255) DEFAULT NULL::character varying,
    database_name character varying(50) DEFAULT ''::character varying NOT NULL,
    is_accepted_name smallint DEFAULT 0::smallint,
    database_id integer
);


ALTER TABLE col.families OWNER TO mol;

--
-- TOC entry 1524 (class 1259 OID 16608)
-- Dependencies: 1837 1838 1839 1840 1841 1842 1843 1844 1845 7
-- Name: scientific_names; Type: TABLE; Schema: col; Owner: mol; Tablespace: mol_tablespace
--

CREATE TABLE scientific_names (
    record_id integer NOT NULL,
    name_code character varying(42) DEFAULT ''::character varying NOT NULL,
    web_site text,
    genus character varying(50) DEFAULT ''::character varying NOT NULL,
    species character varying(50) DEFAULT ''::character varying,
    infraspecies character varying(50) DEFAULT ''::character varying,
    infraspecies_marker character varying(50) DEFAULT NULL::character varying,
    author character varying(100) DEFAULT NULL::character varying,
    accepted_name_code character varying(36) DEFAULT NULL::character varying,
    comment text,
    scrutiny_date text,
    sp2000_status_id smallint,
    database_id integer DEFAULT 0 NOT NULL,
    specialist_id integer,
    family_id integer,
    is_accepted_name smallint DEFAULT 0::smallint NOT NULL
);


ALTER TABLE col.scientific_names OWNER TO mol;

--
-- TOC entry 1522 (class 1259 OID 16419)
-- Dependencies: 1818 1819 1820 1821 1822 1823 1824 1825 1826 1827 7
-- Name: taxa; Type: TABLE; Schema: col; Owner: mol; Tablespace: mol_tablespace
--

CREATE TABLE taxa (
    record_id integer NOT NULL,
    lsid character varying(83) DEFAULT NULL::character varying,
    name character varying(137) DEFAULT ''::character varying NOT NULL,
    name_with_italics character varying(151) DEFAULT ''::character varying NOT NULL,
    taxon character varying(12) DEFAULT ''::character varying NOT NULL,
    name_code character varying(42) DEFAULT NULL::character varying,
    parent_id integer DEFAULT 0 NOT NULL,
    sp2000_status_id smallint DEFAULT 0::smallint NOT NULL,
    database_id smallint DEFAULT 0::smallint NOT NULL,
    is_accepted_name smallint DEFAULT 0::smallint NOT NULL,
    is_species_or_nonsynonymic_higher_taxon smallint DEFAULT 0::smallint NOT NULL
);


ALTER TABLE col.taxa OWNER TO mol;

--
-- TOC entry 1525 (class 1259 OID 16809)
-- Dependencies: 1623 7
-- Name: vw_vert_families; Type: VIEW; Schema: col; Owner: mol
--

CREATE VIEW vw_vert_families AS
    SELECT families.record_id, families.hierarchy_code, families.kingdom, families.phylum, families.class, families.taxonorder AS "order", families.family, families.superfamily, families.family_common_name, families.database_name, families.is_accepted_name, families.database_id FROM families WHERE (((families.class)::text = 'Amphibia'::text) OR ((families.class)::text = 'Mammalia'::text)) ORDER BY families.taxonorder;


ALTER TABLE col.vw_vert_families OWNER TO mol;

--
-- TOC entry 1879 (class 0 OID 0)
-- Dependencies: 1525
-- Name: VIEW vw_vert_families; Type: COMMENT; Schema: col; Owner: mol
--

COMMENT ON VIEW vw_vert_families IS 'This view selects family names from Catalog of Life

It is currently restricted to the orders Mammalia and Amphibia, but will be extended to the rest of veretebrates as required.';


--
-- TOC entry 1526 (class 1259 OID 16813)
-- Dependencies: 1624 7
-- Name: vw_vert_scientific_names; Type: VIEW; Schema: col; Owner: mol
--

CREATE VIEW vw_vert_scientific_names AS
    SELECT s.record_id, s.name_code, s.web_site, s.genus, s.species, s.infraspecies, s.infraspecies_marker, s.author, s.accepted_name_code, s.comment, s.scrutiny_date, s.sp2000_status_id, s.database_id, s.specialist_id, s.family_id, f.family, f.class, s.is_accepted_name FROM (scientific_names s JOIN vw_vert_families f ON ((s.family_id = f.record_id)));


ALTER TABLE col.vw_vert_scientific_names OWNER TO mol;

--
-- TOC entry 1881 (class 0 OID 0)
-- Dependencies: 1526
-- Name: VIEW vw_vert_scientific_names; Type: COMMENT; Schema: col; Owner: mol
--

COMMENT ON VIEW vw_vert_scientific_names IS 'This view selects all columns from the scientific_names table in Catalog of Life.  The set of taxa covered is defined by vw_vert_families';


--
-- TOC entry 1527 (class 1259 OID 16821)
-- Dependencies: 1625 7
-- Name: vw_vert_species; Type: VIEW; Schema: col; Owner: mol
--

CREATE VIEW vw_vert_species AS
    SELECT a.record_id, a.name_code, b.name, a.genus, a.species FROM (vw_vert_scientific_names a JOIN taxa b ON (((a.name_code)::text = (b.name_code)::text))) WHERE ((a.is_accepted_name = 1) AND ((b.taxon)::text = 'Species'::text)) ORDER BY b.name;


ALTER TABLE col.vw_vert_species OWNER TO mol;

--
-- TOC entry 1883 (class 0 OID 0)
-- Dependencies: 1527
-- Name: VIEW vw_vert_species; Type: COMMENT; Schema: col; Owner: mol
--

COMMENT ON VIEW vw_vert_species IS 'Lists accepted species names from Catalogue of Life.  The range of taxa covered is defined by vw_vert_families';


--
-- TOC entry 1528 (class 1259 OID 16826)
-- Dependencies: 1626 7
-- Name: vw_vert_species_and_synonyms; Type: VIEW; Schema: col; Owner: mol
--

CREATE VIEW vw_vert_species_and_synonyms AS
    SELECT DISTINCT b.record_id, b.name_code, b.name AS accepted_name, ((((a.genus)::text || ' '::text) || (a.species)::text) || CASE WHEN (a.infraspecies IS NOT NULL) THEN (' '::text || (a.infraspecies)::text) ELSE ''::text END) AS name, CASE WHEN ((a.name_code)::text = (b.name_code)::text) THEN 'accepted'::text ELSE 'synonym'::text END AS name_status, a.is_accepted_name, a.class, a.family FROM (vw_vert_scientific_names a JOIN vw_vert_species b ON (((a.accepted_name_code)::text = (b.name_code)::text))) ORDER BY b.name, CASE WHEN ((a.name_code)::text = (b.name_code)::text) THEN 'accepted'::text ELSE 'synonym'::text END;


ALTER TABLE col.vw_vert_species_and_synonyms OWNER TO mol;

--
-- TOC entry 1885 (class 0 OID 0)
-- Dependencies: 1528
-- Name: VIEW vw_vert_species_and_synonyms; Type: COMMENT; Schema: col; Owner: mol
--

COMMENT ON VIEW vw_vert_species_and_synonyms IS 'Lists accepted species names and synonymns from Catalogue of Life.  There is a row for each name, identified as accepted or synonym.  The range of taxa covered is defined by vw_vert_families';


--
-- TOC entry 1859 (class 2606 OID 16544)
-- Dependencies: 1523 1523
-- Name: family_record_id_pkey; Type: CONSTRAINT; Schema: col; Owner: mol; Tablespace: mol_tablespace
--

ALTER TABLE ONLY families
    ADD CONSTRAINT family_record_id_pkey PRIMARY KEY (record_id);


--
-- TOC entry 1870 (class 2606 OID 16624)
-- Dependencies: 1524 1524
-- Name: sciname_record_id_pkey; Type: CONSTRAINT; Schema: col; Owner: mol; Tablespace: mol_tablespace
--

ALTER TABLE ONLY scientific_names
    ADD CONSTRAINT sciname_record_id_pkey PRIMARY KEY (record_id);


--
-- TOC entry 1854 (class 2606 OID 16433)
-- Dependencies: 1522 1522
-- Name: taxa_pkey; Type: CONSTRAINT; Schema: col; Owner: mol; Tablespace: mol_tablespace
--

ALTER TABLE ONLY taxa
    ADD CONSTRAINT taxa_pkey PRIMARY KEY (record_id);


--
-- TOC entry 1865 (class 1259 OID 16627)
-- Dependencies: 1524
-- Name: accepted_name_code_idx; Type: INDEX; Schema: col; Owner: mol; Tablespace: mol_tablespace
--

CREATE INDEX accepted_name_code_idx ON scientific_names USING btree (accepted_name_code);


SET default_tablespace = '';

--
-- TOC entry 1856 (class 1259 OID 16547)
-- Dependencies: 1523
-- Name: class_idx; Type: INDEX; Schema: col; Owner: mol; Tablespace: 
--

CREATE INDEX class_idx ON families USING btree (class);


--
-- TOC entry 1846 (class 1259 OID 16437)
-- Dependencies: 1522
-- Name: database_id; Type: INDEX; Schema: col; Owner: mol; Tablespace: 
--

CREATE INDEX database_id ON taxa USING btree (database_id);


--
-- TOC entry 1857 (class 1259 OID 16549)
-- Dependencies: 1523
-- Name: family_idx; Type: INDEX; Schema: col; Owner: mol; Tablespace: 
--

CREATE INDEX family_idx ON families USING btree (family);


--
-- TOC entry 1847 (class 1259 OID 16439)
-- Dependencies: 1522
-- Name: is_accepted_name; Type: INDEX; Schema: col; Owner: mol; Tablespace: 
--

CREATE INDEX is_accepted_name ON taxa USING btree (is_accepted_name);


--
-- TOC entry 1860 (class 1259 OID 16551)
-- Dependencies: 1523
-- Name: is_accepted_name_idx; Type: INDEX; Schema: col; Owner: mol; Tablespace: 
--

CREATE INDEX is_accepted_name_idx ON families USING btree (is_accepted_name);


--
-- TOC entry 1848 (class 1259 OID 16441)
-- Dependencies: 1522
-- Name: is_species_or_nonsynonymic_higher_taxon; Type: INDEX; Schema: col; Owner: mol; Tablespace: 
--

CREATE INDEX is_species_or_nonsynonymic_higher_taxon ON taxa USING btree (is_species_or_nonsynonymic_higher_taxon);


--
-- TOC entry 1861 (class 1259 OID 16545)
-- Dependencies: 1523
-- Name: kingdom_idx; Type: INDEX; Schema: col; Owner: mol; Tablespace: 
--

CREATE INDEX kingdom_idx ON families USING btree (kingdom);


--
-- TOC entry 1849 (class 1259 OID 16434)
-- Dependencies: 1522 1522 1522 1522
-- Name: name; Type: INDEX; Schema: col; Owner: mol; Tablespace: 
--

CREATE INDEX name ON taxa USING btree (name, is_species_or_nonsynonymic_higher_taxon, database_id, sp2000_status_id);


--
-- TOC entry 1850 (class 1259 OID 16440)
-- Dependencies: 1522
-- Name: name_code; Type: INDEX; Schema: col; Owner: mol; Tablespace: 
--

CREATE INDEX name_code ON taxa USING btree (name_code);


--
-- TOC entry 1866 (class 1259 OID 16628)
-- Dependencies: 1524 1524
-- Name: name_code_idx; Type: INDEX; Schema: col; Owner: mol; Tablespace: 
--

CREATE INDEX name_code_idx ON scientific_names USING btree (name_code, family_id);


--
-- TOC entry 1851 (class 1259 OID 16436)
-- Dependencies: 1522
-- Name: parent_id; Type: INDEX; Schema: col; Owner: mol; Tablespace: 
--

CREATE INDEX parent_id ON taxa USING btree (parent_id);


--
-- TOC entry 1862 (class 1259 OID 16546)
-- Dependencies: 1523
-- Name: phylum_idx; Type: INDEX; Schema: col; Owner: mol; Tablespace: 
--

CREATE INDEX phylum_idx ON families USING btree (phylum);


--
-- TOC entry 1867 (class 1259 OID 16625)
-- Dependencies: 1524
-- Name: sciname_family_idx; Type: INDEX; Schema: col; Owner: mol; Tablespace: 
--

CREATE INDEX sciname_family_idx ON scientific_names USING btree (family_id);


SET default_tablespace = mol_tablespace;

--
-- TOC entry 1868 (class 1259 OID 16820)
-- Dependencies: 1524
-- Name: sciname_is_accepted_name_idx; Type: INDEX; Schema: col; Owner: mol; Tablespace: mol_tablespace
--

CREATE INDEX sciname_is_accepted_name_idx ON scientific_names USING btree (is_accepted_name);


SET default_tablespace = '';

--
-- TOC entry 1852 (class 1259 OID 16435)
-- Dependencies: 1522
-- Name: sp2000_status_id; Type: INDEX; Schema: col; Owner: mol; Tablespace: 
--

CREATE INDEX sp2000_status_id ON taxa USING btree (sp2000_status_id);


--
-- TOC entry 1871 (class 1259 OID 16626)
-- Dependencies: 1524
-- Name: species_idx; Type: INDEX; Schema: col; Owner: mol; Tablespace: 
--

CREATE INDEX species_idx ON scientific_names USING btree (species);


--
-- TOC entry 1863 (class 1259 OID 16550)
-- Dependencies: 1523
-- Name: superfamily_idx; Type: INDEX; Schema: col; Owner: mol; Tablespace: 
--

CREATE INDEX superfamily_idx ON families USING btree (superfamily);


--
-- TOC entry 1855 (class 1259 OID 16438)
-- Dependencies: 1522
-- Name: taxon; Type: INDEX; Schema: col; Owner: mol; Tablespace: 
--

CREATE INDEX taxon ON taxa USING btree (taxon);


--
-- TOC entry 1864 (class 1259 OID 16548)
-- Dependencies: 1523
-- Name: taxonorder_idx; Type: INDEX; Schema: col; Owner: mol; Tablespace: 
--

CREATE INDEX taxonorder_idx ON families USING btree (taxonorder);


--
-- TOC entry 1875 (class 0 OID 0)
-- Dependencies: 7
-- Name: col; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA col FROM PUBLIC;
REVOKE ALL ON SCHEMA col FROM postgres;
GRANT ALL ON SCHEMA col TO postgres;
GRANT ALL ON SCHEMA col TO mol;


--
-- TOC entry 1876 (class 0 OID 0)
-- Dependencies: 1523
-- Name: families; Type: ACL; Schema: col; Owner: mol
--

REVOKE ALL ON TABLE families FROM PUBLIC;
REVOKE ALL ON TABLE families FROM mol;
GRANT ALL ON TABLE families TO mol;
GRANT ALL ON TABLE families TO postgres;
GRANT SELECT ON TABLE families TO mol_query;
GRANT SELECT,INSERT,REFERENCES,DELETE,TRUNCATE,UPDATE ON TABLE families TO mol_user;


--
-- TOC entry 1877 (class 0 OID 0)
-- Dependencies: 1524
-- Name: scientific_names; Type: ACL; Schema: col; Owner: mol
--

REVOKE ALL ON TABLE scientific_names FROM PUBLIC;
REVOKE ALL ON TABLE scientific_names FROM mol;
GRANT ALL ON TABLE scientific_names TO mol;
GRANT SELECT ON TABLE scientific_names TO mol_query;
GRANT SELECT,INSERT,REFERENCES,DELETE,TRUNCATE,UPDATE ON TABLE scientific_names TO mol_user;


--
-- TOC entry 1878 (class 0 OID 0)
-- Dependencies: 1522
-- Name: taxa; Type: ACL; Schema: col; Owner: mol
--

REVOKE ALL ON TABLE taxa FROM PUBLIC;
REVOKE ALL ON TABLE taxa FROM mol;
GRANT ALL ON TABLE taxa TO mol;
GRANT ALL ON TABLE taxa TO postgres;
GRANT SELECT ON TABLE taxa TO mol_query;
GRANT SELECT,INSERT,REFERENCES,DELETE,TRUNCATE,UPDATE ON TABLE taxa TO mol_user;


--
-- TOC entry 1880 (class 0 OID 0)
-- Dependencies: 1525
-- Name: vw_vert_families; Type: ACL; Schema: col; Owner: mol
--

REVOKE ALL ON TABLE vw_vert_families FROM PUBLIC;
REVOKE ALL ON TABLE vw_vert_families FROM mol;
GRANT ALL ON TABLE vw_vert_families TO mol;
GRANT SELECT ON TABLE vw_vert_families TO mol_query;


--
-- TOC entry 1882 (class 0 OID 0)
-- Dependencies: 1526
-- Name: vw_vert_scientific_names; Type: ACL; Schema: col; Owner: mol
--

REVOKE ALL ON TABLE vw_vert_scientific_names FROM PUBLIC;
REVOKE ALL ON TABLE vw_vert_scientific_names FROM mol;
GRANT ALL ON TABLE vw_vert_scientific_names TO mol;
GRANT SELECT,INSERT,REFERENCES,DELETE,TRUNCATE,UPDATE ON TABLE vw_vert_scientific_names TO mol_user;


--
-- TOC entry 1884 (class 0 OID 0)
-- Dependencies: 1527
-- Name: vw_vert_species; Type: ACL; Schema: col; Owner: mol
--

REVOKE ALL ON TABLE vw_vert_species FROM PUBLIC;
REVOKE ALL ON TABLE vw_vert_species FROM mol;
GRANT ALL ON TABLE vw_vert_species TO mol;
GRANT SELECT ON TABLE vw_vert_species TO mol_query;
GRANT SELECT,INSERT,REFERENCES,DELETE,TRUNCATE,UPDATE ON TABLE vw_vert_species TO mol_user;


--
-- TOC entry 1886 (class 0 OID 0)
-- Dependencies: 1528
-- Name: vw_vert_species_and_synonyms; Type: ACL; Schema: col; Owner: mol
--

REVOKE ALL ON TABLE vw_vert_species_and_synonyms FROM PUBLIC;
REVOKE ALL ON TABLE vw_vert_species_and_synonyms FROM mol;
GRANT ALL ON TABLE vw_vert_species_and_synonyms TO mol;
GRANT SELECT ON TABLE vw_vert_species_and_synonyms TO mol_query;
GRANT SELECT,INSERT,REFERENCES,DELETE,TRUNCATE,UPDATE ON TABLE vw_vert_species_and_synonyms TO mol_user;


-- Completed on 2011-04-21 17:25:44 EDT

--
-- PostgreSQL database dump complete
--

