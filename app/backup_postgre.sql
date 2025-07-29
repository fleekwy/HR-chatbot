--
-- PostgreSQL database dump
--

-- Dumped from database version 16.9
-- Dumped by pg_dump version 16.9

-- Started on 2025-07-23 18:11:00

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 2 (class 3079 OID 16384)
-- Name: adminpack; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS adminpack WITH SCHEMA pg_catalog;


--
-- TOC entry 4914 (class 0 OID 0)
-- Dependencies: 2
-- Name: EXTENSION adminpack; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION adminpack IS 'administrative functions for PostgreSQL';


--
-- TOC entry 221 (class 1255 OID 16437)
-- Name: log_deleted_sessions(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.log_deleted_sessions() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Сохраняем все tg_id, привязанные к удаляемому логину
    INSERT INTO deleted_sessions_log (login, tg_id)
    SELECT login, tg_id
    FROM sessions
    WHERE login = OLD.login;

    RETURN OLD;
END;
$$;


ALTER FUNCTION public.log_deleted_sessions() OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 220 (class 1259 OID 16431)
-- Name: deleted_sessions_log; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.deleted_sessions_log (
    login text,
    tg_id bigint,
    deleted_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.deleted_sessions_log OWNER TO postgres;

--
-- TOC entry 216 (class 1259 OID 16399)
-- Name: login_table; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.login_table (
    login text NOT NULL,
    is_admin boolean DEFAULT false NOT NULL
);


ALTER TABLE public.login_table OWNER TO postgres;

--
-- TOC entry 219 (class 1259 OID 16417)
-- Name: sessions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.sessions (
    tg_id integer NOT NULL,
    login text NOT NULL
);


ALTER TABLE public.sessions OWNER TO postgres;

--
-- TOC entry 218 (class 1259 OID 16407)
-- Name: statistics_table; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.statistics_table (
    id integer NOT NULL,
    question text NOT NULL,
    answer text,
    answer_date date DEFAULT CURRENT_DATE NOT NULL,
    answer_time real NOT NULL
);


ALTER TABLE public.statistics_table OWNER TO postgres;

--
-- TOC entry 217 (class 1259 OID 16406)
-- Name: statistics-table_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public."statistics-table_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public."statistics-table_id_seq" OWNER TO postgres;

--
-- TOC entry 4915 (class 0 OID 0)
-- Dependencies: 217
-- Name: statistics-table_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public."statistics-table_id_seq" OWNED BY public.statistics_table.id;


--
-- TOC entry 4750 (class 2604 OID 16410)
-- Name: statistics_table id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.statistics_table ALTER COLUMN id SET DEFAULT nextval('public."statistics-table_id_seq"'::regclass);


--
-- TOC entry 4908 (class 0 OID 16431)
-- Dependencies: 220
-- Data for Name: deleted_sessions_log; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.deleted_sessions_log (login, tg_id, deleted_at) FROM stdin;
\.


--
-- TOC entry 4904 (class 0 OID 16399)
-- Dependencies: 216
-- Data for Name: login_table; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.login_table (login, is_admin) FROM stdin;
use3r@example.com	f
user@example.com	t
Daniil.Kondratyuk@waveaccess.global	t
Yaroslav.Bodyakin@waveaccess.global	f
\.


--
-- TOC entry 4907 (class 0 OID 16417)
-- Dependencies: 219
-- Data for Name: sessions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.sessions (tg_id, login) FROM stdin;
1315154517	Daniil.Kondratyuk@waveaccess.global
\.


--
-- TOC entry 4906 (class 0 OID 16407)
-- Dependencies: 218
-- Data for Name: statistics_table; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.statistics_table (id, question, answer, answer_date, answer_time) FROM stdin;
1	Кто основал компанию?	Илья Фейгин и Андрей Низвоский - основатели компании, Илья так же является СТО, а Андрей операционным и коммерческим директором. Далее - Александр Азаров, который присоединился к компании в 2004 году в возрасте 18 лет и на данный момент является вице-президентом по разработке ПП. Так же он отвечает за HR блок. Ну, и Наталия Разумейко, в чьём ведении находится всё финансовое подразделение компании.	2025-07-23	9.69
2	e24q35	Какой адрес у офиса в Воронеже? ул. Свободы 14, этаж 9, оф 907.	2025-07-23	4.23
3	e24q35	Какой адрес у офиса в Воронеже? ул. Свободы 14, этаж 9, оф 907.	2025-07-23	3.95
4	e24q36	Вопрос не ясен. Переформулируйте, указав контекст.	2025-07-23	3.89
5	e24q35	Какой адрес у офиса в Воронеже? ул. Свободы 14, этаж 9, оф 907.	2025-07-23	3.76
\.


--
-- TOC entry 4916 (class 0 OID 0)
-- Dependencies: 217
-- Name: statistics-table_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public."statistics-table_id_seq"', 5, true);


--
-- TOC entry 4754 (class 2606 OID 16425)
-- Name: login_table login_table_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.login_table
    ADD CONSTRAINT login_table_pkey PRIMARY KEY (login);


--
-- TOC entry 4758 (class 2606 OID 16423)
-- Name: sessions sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT sessions_pkey PRIMARY KEY (tg_id);


--
-- TOC entry 4756 (class 2606 OID 16415)
-- Name: statistics_table table_name_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.statistics_table
    ADD CONSTRAINT table_name_pkey PRIMARY KEY (id);


--
-- TOC entry 4760 (class 2620 OID 16438)
-- Name: login_table before_delete_login_log_sessions; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER before_delete_login_log_sessions BEFORE DELETE ON public.login_table FOR EACH ROW EXECUTE FUNCTION public.log_deleted_sessions();


--
-- TOC entry 4759 (class 2606 OID 16426)
-- Name: sessions ее; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT "ее" FOREIGN KEY (login) REFERENCES public.login_table(login) ON DELETE CASCADE NOT VALID;


-- Completed on 2025-07-23 18:11:00

--
-- PostgreSQL database dump complete
--

