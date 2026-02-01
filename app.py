import streamlit as st
import pandas as pd
from thefuzz import process, fuzz
import database
import utils
import backup
import audit
import dashboard
from datetime import date
from io import StringIO
import json
import os
import re

st.set_page_config(page_title="Challenge Raids Orientation", layout="wide")

database.init_db()


def main():
    # Sauvegarde automatique quotidienne
    if backup.should_backup_today():
        backup.create_backup()
    
    st.sidebar.title("Navigation")
    pages = ["Import", "Édition", "Classement"]
    selection = st.sidebar.radio("Aller vers", pages)

    if selection == "Import":
        show_import()
    elif selection == "Édition":
        show_edition()
    elif selection == "Classement":
        show_ranking()


def read_uploaded_file(uploaded_file) -> pd.DataFrame:
    """Lire un fichier CSV ou XLSX en DataFrame."""
    name = uploaded_file.name.lower()
    try:
        if name.endswith(".xlsx") or name.endswith(".xls"):  # excel
            return pd.read_excel(uploaded_file)
        elif name.endswith(".csv"):  # csv
            # Essaie utf-8 puis cp1252
            try:
                return pd.read_csv(uploaded_file)
            except UnicodeDecodeError:
                uploaded_file.seek(0)
                return pd.read_csv(
                    uploaded_file, encoding="cp1252", sep=None, engine="python"
                )
        else:
            raise ValueError("Format de fichier non supporté. Utilisez .xlsx ou .csv")
    except Exception as e:
        raise e


def show_import():
    st.title("Import des Résultats")

    # Création/gestion des challenges avant l'upload
    st.subheader("Créer nouveau challenge")
    with st.form("new_challenge_form_import"):
        range_input = st.text_input("Range (YYYY-YYYY)", placeholder="2025-2026")
        if st.form_submit_button("Ajouter le challenge"):
            import re as _re

            m = _re.match(r"^\s*(\d{4})\s*-\s*(\d{4})\s*$", range_input)
            if m:
                start = int(m.group(1))
                end = int(m.group(2))
                if end == start + 1:
                    try:
                        database.create_challenge(range_input, start, end)
                        st.success(f"Challenge '{range_input}' enregistré en base.")
                        st.rerun()
                    except Exception as e:
                        st.warning(f"Erreur : {e}")
                else:
                    st.error(
                        "La plage doit être du type YYYY-YYYY avec année suivante."
                    )
            else:
                st.error("Format invalide. Utilisez 2025-2026.")

    with st.expander("🗑️ Supprimer un challenge existant"):
        del_challenges = database.get_challenges()
        if del_challenges:
            del_map = {c["id"]: c["range"] for c in del_challenges}
            id_to_del = st.selectbox("Sélectionner le challenge à supprimer", options=list(del_map.keys()), format_func=lambda x: del_map[x], key="del_ch_select")
            st.warning("⚠️ Attention : Cette action est irréversible. Elle supprimera le challenge ainsi que tous les raids et résultats associés.")
            if st.button("Supprimer définitivement ce challenge", type="primary"):
                database.delete_challenge(id_to_del)
                st.success("Challenge supprimé.")
                st.rerun()
        else:
            st.info("Aucun challenge à supprimer.")

    st.divider()
    challenges = database.get_challenges()
    if challenges:
        ch_map = {str(c["id"]): c["range"] for c in challenges}
        sel_id = st.selectbox(
            "Choisir le challenge pour ce fichier",
            options=list(ch_map.keys()),
            format_func=lambda k: ch_map[k],
        )
        st.session_state.import_selected_challenge = sel_id
        matching = next((c for c in challenges if str(c["id"]) == sel_id), None)
        if matching:
            st.session_state.import_challenge_date = date(matching["start"], 1, 1)
    else:
        st.info("Aucun challenge existant. Créez-en un ci-dessus.")

    # Sélection du circuit (canonique)
    circuit = st.selectbox("Circuit", ["trotteur", "orienteur", "raideur"])

    uploaded_file = st.file_uploader(
        "Choisir un fichier (.xlsx ou .csv)", type=["xlsx", "csv"]
    )

    if uploaded_file:
        try:
            df = read_uploaded_file(uploaded_file)
            if df.empty:
                st.warning("Le fichier est vide.")
                return

            st.write("Aperçu du fichier :")
            st.dataframe(df.head())

            st.subheader("Configuration de l'import")
            col1, col2 = st.columns(2)
            with col1:
                nom_event = st.text_input("Nom de l'événement", "Raid Inconnu")
            with col2:
                default_date = st.session_state.get(
                    "import_challenge_date", date.today()
                )
                date_event = st.date_input("Date de la course", default_date, format="DD/MM/YYYY")

            st.markdown("### Mapping des colonnes — équipes (1 à 3 coéquipiers)")
            cols = df.columns.tolist()

            # Coéquipier 1 (obligatoire)
            st.markdown("#### Coéquipier 1")
            mode1 = st.radio(
                "Mode noms 1",
                ["Colonnes séparées", "Une seule colonne (Nom Prénom)"],
                index=0,
                horizontal=True,
                key="mode1",
            )
            if mode1 == "Colonnes séparées":
                c1, c2 = st.columns(2)
                col_prenom1 = c1.selectbox("Prénom 1", cols, index=0)
                col_nom1 = c2.selectbox("Nom 1", cols, index=min(1, len(cols) - 1))
                name_map_1 = {"mode": "split", "prenom": col_prenom1, "nom": col_nom1}
            else:
                col_fullname1 = st.selectbox("Colonne Nom Prénom 1", cols, index=0)
                name_map_1 = {"mode": "single", "full": col_fullname1}

            col_classement = st.selectbox(
                "Classement (rang dans la catégorie)", cols, index=min(2, len(cols) - 1)
            )
            # Points et catégorie (définis pour Coéquipier 1 et appliqués à tous)
            col_points = st.selectbox(
                "Colonne Points (optionnel)", ["Aucune"] + cols, index=0
            )
            col_categorie = st.selectbox(
                "Colonne Catégorie", cols, index=min(3, len(cols) - 1)
            )

            # Coéquipier 2
            st.markdown("#### Coéquipier 2 (optionnel)")
            mode2 = st.radio(
                "Mode noms 2",
                ["Aucun", "Colonnes séparées", "Une seule colonne (Nom Prénom)"],
                index=0,
                horizontal=True,
                key="mode2",
            )
            name_map_2 = None
            if mode2 == "Colonnes séparées":
                d1, d2 = st.columns(2)
                col_prenom2 = d1.selectbox("Prénom 2", cols, index=0)
                col_nom2 = d2.selectbox("Nom 2", cols, index=0)
                name_map_2 = {"mode": "split", "prenom": col_prenom2, "nom": col_nom2}
            elif mode2 == "Une seule colonne (Nom Prénom)":
                col_fullname2 = st.selectbox("Colonne Nom Prénom 2", cols, index=0)
                name_map_2 = {"mode": "single", "full": col_fullname2}

            # Coéquipier 3
            st.markdown("#### Coéquipier 3 (optionnel)")
            mode3 = st.radio(
                "Mode noms 3",
                ["Aucun", "Colonnes séparées", "Une seule colonne (Nom Prénom)"],
                index=0,
                horizontal=True,
                key="mode3",
            )
            name_map_3 = None
            if mode3 == "Colonnes séparées":
                e1, e2 = st.columns(2)
                col_prenom3 = e1.selectbox("Prénom 3", cols, index=0)
                col_nom3 = e2.selectbox("Nom 3", cols, index=0)
                name_map_3 = {"mode": "split", "prenom": col_prenom3, "nom": col_nom3}
            elif mode3 == "Une seule colonne (Nom Prénom)":
                col_fullname3 = st.selectbox("Colonne Nom Prénom 3", cols, index=0)
                name_map_3 = {"mode": "single", "full": col_fullname3}

            if st.button("Analyser l'import"):
                # Vérifier si le raid existe déjà
                existing_course = database.run_query(
                    "SELECT id, nom_course FROM courses WHERE nom_course = ? AND date = ? AND circuit = ? AND challenge_id = ?",
                    (nom_event, str(date_event), circuit, st.session_state.get("import_selected_challenge"))
                )
                
                if not existing_course.empty:
                    st.error(f"⚠️ Le raid '{nom_event}' du {date_event.strftime('%d/%m/%Y')} pour le circuit {circuit} existe déjà !")
                    st.warning("🚫 Import annulé pour éviter les doublons.")
                    return
                
                name_mappings = [name_map_1]
                if name_map_2:
                    name_mappings.append(name_map_2)
                if name_map_3:
                    name_mappings.append(name_map_3)

                analyze_file(
                    df=df,
                    name_mappings=name_mappings,
                    col_classement=col_classement,
                    col_points=None if col_points == "Aucune" else col_points,
                    col_categorie=col_categorie,
                    circuit=circuit,
                    nom_event=nom_event,
                    date_event=date_event,
                    challenge_id=st.session_state.get("import_selected_challenge"),
                )
        except Exception as e:
            st.error(f"Erreur lors de la lecture: {e}")

    if "import_data" in st.session_state:
        show_validation_interface()


def normalize_name(s: str) -> str:
    if pd.isna(s) or s is None:
        return ""
    result = str(s).strip()
    return "" if result.lower() == "nan" else result


def normalize_category(val):
    """Normalise les catégories (H -> Homme, F -> Femme, M -> Mixte)."""
    if val is None or pd.isna(val):
        return None
    v = str(val).strip().upper()  # Conversion en majuscules pour simplifier
    if not v:
        return None
    
    # Détection Homme
    if v in ["H", "HOMME", "HOMMES", "MASCULIN", "MEN", "MALE"]:
        return "Homme"
    # Détection Femme  
    if v in ["F", "FEMME", "FEMMES", "DAME", "DAMES", "FÉMININE", "FEMININE", "WOMEN", "FEMALE"]:
        return "Femme"
    # Détection Mixte
    if v in ["M", "MIXTE", "MIXTES", "MIXED", "MIX"]:
        return "Mixte"
    
    # Si aucune correspondance, retourner la valeur originale
    return v


def check_category_match(val, target_cat):
    """Vérifie si la catégorie val correspond au filtre target_cat (ex: 'H' -> 'Homme')."""
    v = str(val).lower().strip()
    t = target_cat.lower()
    if t == "homme":
        return "homme" in v or "masculin" in v or re.search(r"\bh\b", v) is not None
    if t == "femme":
        return "femme" in v or "féminine" in v or "dame" in v or re.search(r"\bf\b", v) is not None
    if t == "mixte":
        return "mixte" in v or re.search(r"\bm\b", v) is not None
    return t in v


def format_date_fr(date_str: str) -> str:
    """Convertit YYYY-MM-DD en DD/MM/YY pour l'affichage."""
    if not date_str:
        return ""
    try:
        parts = date_str.split("-")
        if len(parts) == 3:
            year = parts[0][-2:]  # Prendre les 2 derniers chiffres de l'année
            return f"{parts[2]}/{parts[1]}/{year}"
    except:
        pass
    return date_str


def analyze_file(
    df: pd.DataFrame,
    name_mappings: list,
    col_classement: str,
    col_points: str | None,
    col_categorie: str | None,
    circuit: str,
    nom_event: str,
    date_event,
    challenge_id=None,
):
    # Détection des conflits entre classement et points
    if col_points:
        conflicts_detected = []
        for idx, row in df.iterrows():
            try:
                rang = int(row.get(col_classement))
                points_fichier = int(row.get(col_points))
                
                # Calculer les points attendus selon le rang
                if col_categorie:
                    # Utiliser le rang par catégorie si possible
                    temp_df = df.copy()
                    temp_df["_temp_sort_rank"] = pd.to_numeric(temp_df[col_classement], errors='coerce')
                    valid_ranks_df = temp_df.dropna(subset=["_temp_sort_rank"]).copy()
                    
                    if not valid_ranks_df.empty:
                        valid_ranks_df["_temp_cat"] = valid_ranks_df[col_categorie].apply(normalize_category)
                        valid_ranks_df = valid_ranks_df.sort_values("_temp_sort_rank")
                        valid_ranks_df["_calc_cat_rank"] = valid_ranks_df.groupby("_temp_cat").cumcount() + 1
                        
                        if idx in valid_ranks_df.index:
                            rang_categorie = valid_ranks_df.loc[idx, "_calc_cat_rank"]
                            points_attendus = utils.calculate_points(rang_categorie)
                        else:
                            points_attendus = utils.calculate_points(rang)
                    else:
                        points_attendus = utils.calculate_points(rang)
                else:
                    points_attendus = utils.calculate_points(rang)
                
                # Vérifier s'il y a conflit
                if points_fichier != points_attendus:
                    conflicts_detected.append({
                        'ligne': idx + 1,
                        'rang': rang,
                        'points_fichier': points_fichier,
                        'points_attendus': points_attendus
                    })
            except (ValueError, TypeError):
                continue
        
        # Afficher les conflits détectés
        if conflicts_detected:
            st.error(f"⚠️ {len(conflicts_detected)} conflits détectés entre classement et points !")
            
            with st.expander("🔍 Voir les conflits détectés"):
                for conflict in conflicts_detected[:10]:  # Limiter à 10 pour l'affichage
                    st.warning(
                        f"Ligne {conflict['ligne']}: Rang {conflict['rang']} → "
                        f"Points fichier: {conflict['points_fichier']}, "
                        f"Points attendus: {conflict['points_attendus']}"
                    )
                if len(conflicts_detected) > 10:
                    st.info(f"... et {len(conflicts_detected) - 10} autres conflits")
            
            st.markdown("**⚙️ Choisissez la source de données à privilégier :**")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🏅 Utiliser les classements (recalculer les points)", use_container_width=True):
                    st.session_state['import_use_ranks'] = True
                    st.rerun()
            with col2:
                if st.button("⭐ Utiliser les points du fichier (ignorer classements)", use_container_width=True):
                    st.session_state['import_use_points'] = True
                    st.rerun()
            
            st.info("📝 **Recommandation :** Utilisez les classements si vous êtes sûr de leur exactitude, sinon utilisez les points du fichier.")
            return  # Arrêter ici jusqu'à ce que l'utilisateur choisisse
    # Liste des coureurs existants (nom_complet)
    existing_coureurs = database.get_all_coureurs()
    existing_names_by_id = {id_: name for id_, name in existing_coureurs}
    existing_names = list(existing_names_by_id.values())
    
    # Si aucun raid n'existe, nettoyer automatiquement les coureurs orphelins
    if existing_names:
        total_courses = database.run_query("SELECT COUNT(*) as count FROM courses").iloc[0]['count']
        if total_courses == 0:
            st.info(f"🧹 Nettoyage automatique de {len(existing_names)} coureurs orphelins...")
            deleted_count = database.clean_invalid_coureurs()
            st.success(f"✅ {deleted_count} coureurs orphelins supprimés automatiquement.")
            # Recharger la liste des coureurs après nettoyage
            existing_coureurs = database.get_all_coureurs()
            existing_names_by_id = {id_: name for id_, name in existing_coureurs}
            existing_names = list(existing_names_by_id.values())

    # Pré-calcul des rangs par catégorie pour l'attribution correcte des points
    # (ex: 10e au scratch mais 1ere Femme -> doit avoir les points du 1er)
    calculated_cat_ranks = {}
    if col_categorie and col_classement:
        try:
            temp_df = df.copy()
            # Conversion numérique du classement pour trier correctement
            temp_df["_temp_sort_rank"] = pd.to_numeric(temp_df[col_classement], errors='coerce')
            
            # On ne garde que les lignes avec un classement valide pour déterminer l'ordre
            valid_ranks_df = temp_df.dropna(subset=["_temp_sort_rank"]).copy()
            
            if not valid_ranks_df.empty:
                # Nettoyage et normalisation de la catégorie
                valid_ranks_df["_temp_cat"] = valid_ranks_df[col_categorie].apply(normalize_category)
                # Tri par classement scratch
                valid_ranks_df = valid_ranks_df.sort_values("_temp_sort_rank")
                # Calcul du rang au sein de chaque catégorie (1, 2, 3...)
                valid_ranks_df["_calc_cat_rank"] = valid_ranks_df.groupby("_temp_cat").cumcount() + 1
                # Mapping index ligne -> rang catégorie
                calculated_cat_ranks = valid_ranks_df["_calc_cat_rank"].to_dict()
        except Exception:
            pass

    to_process = []
    progress_bar = st.progress(0)

    for idx, row in df.iterrows():
        # Classement (rang)
        try:
            rang = int(row.get(col_classement))
        except Exception:
            rang = 999  # défaut

        # Points: soit la colonne, soit calculés à partir du rang
        points = 0
        points_calculated = False
        if col_points:
            try:
                points = int(row.get(col_points))
                points_calculated = True
                
                # Respecter le choix de l'utilisateur en cas de conflit
                if st.session_state.get('import_use_ranks', False):
                    # Forcer le recalcul des points selon le rang
                    points_calculated = False
                elif st.session_state.get('import_use_points', False):
                    # Garder les points du fichier
                    points_calculated = True
            except Exception:
                pass
        
        if not points_calculated:
            # Si on a pu calculer un rang par catégorie, on l'utilise pour les points
            if idx in calculated_cat_ranks:
                points = utils.calculate_points(calculated_cat_ranks[idx])
            else:
                # ATTENTION: Sans catégorie définie, impossible de calculer correctement les points
                # On met 1 point par défaut pour éviter les incohérences
                points = 1  # Points minimum au lieu d'utiliser le rang scratch

        # Catégorie à appliquer à tous les coéquipiers de la ligne
        if col_categorie:
            try:
                categorie = normalize_category(row.get(col_categorie))
            except Exception:
                categorie = None
        else:
            categorie = None

        # Pour chaque coéquipier mappé, créer une entrée
        for mapping in name_mappings:
            if mapping.get("mode") == "split":
                prenom = normalize_name(row.get(mapping.get("prenom"), ""))
                nom = normalize_name(row.get(mapping.get("nom"), ""))
                full_name = f"{prenom} {nom}".strip()
            elif mapping.get("mode") == "single":
                full_cell = normalize_name(row.get(mapping.get("full"), ""))
                # Tenter de séparer si possible (dernier token comme nom le plus fréquent "Prénom Nom")
                parts = full_cell.split()
                if len(parts) >= 2:
                    prenom = " ".join(parts[:-1])
                    nom = parts[-1]
                else:
                    prenom, nom = "", full_cell
                full_name = f"{prenom} {nom}".strip()
            else:
                continue

            # Vérifications plus strictes pour éviter les données invalides
            if not full_name or full_name.lower() in ["nan", "nan nan", ""] or pd.isna(full_name):
                continue
            if not prenom or prenom.lower() == "nan" or pd.isna(prenom):
                continue
            if not nom or nom.lower() == "nan" or pd.isna(nom):
                continue

            status = "new"
            match_proposal = None
            score = 0

            if full_name in existing_names:
                status = "exact"
                match_proposal = full_name
                score = 100
            elif existing_names:
                best = process.extractOne(
                    full_name, existing_names, scorer=fuzz.token_sort_ratio
                )
                if best:
                    best_match, score = best
                    if score == 100:
                        status = "exact"
                        match_proposal = best_match
                    elif score >= 88:
                        status = "conflict"
                        match_proposal = best_match
                    else:
                        status = "new"

            to_process.append(
                {
                    "prenom": prenom,
                    "nom": nom,
                    "full_name": full_name,
                    "rang": rang,
                    "points": points,
                    "circuit": circuit,
                    "categorie": categorie,
                    "status": status,
                    "match_proposal": match_proposal,
                    "score": score,
                }
            )

        progress_bar.progress((idx + 1) / len(df))

    st.session_state["import_data"] = to_process
    st.session_state["import_meta"] = {
        "nom_event": nom_event,
        "date": date_event,
        "circuit": circuit,
        "challenge_id": challenge_id,
    }
    
    # Nettoyer les flags de choix utilisateur
    if 'import_use_ranks' in st.session_state:
        del st.session_state['import_use_ranks']
    if 'import_use_points' in st.session_state:
        del st.session_state['import_use_points']
    
    st.rerun()


def show_validation_interface():
    st.divider()
    st.header("Validation des données")
    data = st.session_state["import_data"]
    meta = st.session_state["import_meta"]

    conflicts = [d for d in data if d["status"] == "conflict"]

    st.info(
        f"{len([d for d in data if d['status'] == 'new'])} nouveaux, "
        f"{len([d for d in data if d['status'] == 'exact'])} exacts, "
        f"{len(conflicts)} potentiels doublons."
    )

    with st.form("validation_form"):
        if conflicts:
            st.subheader("Résolution des doublons")
            
            # En-têtes de colonnes pour structurer l'affichage
            h1, h2, h3 = st.columns([3, 3, 4])
            h1.markdown("**Donnée Importée**")
            h2.markdown("**Similaire existant**")
            h3.markdown("**Action**")
            st.divider()

            for i, item in enumerate(conflicts):
                c1, c2, c3 = st.columns([3, 3, 4])
                with c1:
                    st.markdown(f"**{item['full_name']}**")
                    st.caption(f"Rang {item['rang']} | {item['points']} pts")
                with c2:
                    st.markdown(f"**{item['match_proposal']}**")
                    st.caption(f"Score : {item['score']}%")
                with c3:
                    key = f"conflict_{i}"
                    st.radio(
                        "Action",
                        [
                            "Créer Nouveau",
                            f"Valider = même personne ({item['match_proposal']})",
                        ],
                        key=key,
                        label_visibility="collapsed",
                    )
                st.divider()

        if st.form_submit_button("Valider et Sauvegarder"):
            save_results(data, meta, conflicts)


def save_results(data, meta, conflicts):
    # Une course unique pour l'import courant (circuit sélectionné)
    course_id = database.create_course(
        meta["nom_event"], str(meta["date"]), meta["circuit"], meta.get("challenge_id")
    )

    # Mapping nom_complet -> id
    existing_coureurs = dict(database.get_all_coureurs())  # {id, nom}
    name_to_id = {name: id_ for id_, name in existing_coureurs.items()}

    batch_results = []
    count_added = 0
    progress_bar = st.progress(0)
    total_len = len(data)
    for i, item in enumerate(data):
        full_name = item["full_name"]
        coureur_id = None

        if item["status"] == "exact":
            coureur_id = name_to_id.get(item["match_proposal"])
        elif item["status"] == "new":
            coureur_id = database.add_coureur(full_name, None, None)
            name_to_id[full_name] = coureur_id
        elif item["status"] == "conflict":
            widget_key = f"conflict_{conflicts.index(item)}"
            user_choice = st.session_state.get(widget_key)
            if user_choice and "même personne" in user_choice:
                coureur_id = name_to_id.get(item["match_proposal"])
            else:
                coureur_id = database.add_coureur(full_name, None, None)
                name_to_id[full_name] = coureur_id

        if coureur_id:
            # Collecter pour insertion groupée
            batch_results.append((
                course_id,
                coureur_id,
                item["rang"],
                int(item["points"]),
                item.get("categorie"),
            ))
            count_added += 1
        
        if total_len > 0:
            progress_bar.progress((i + 1) / total_len)

    if batch_results:
        database.add_results_batch(batch_results)

    st.success(f"{count_added} résultats importés.")
    if "import_data" in st.session_state:
        del st.session_state["import_data"]
    if "import_meta" in st.session_state:
        del st.session_state["import_meta"]


def show_ranking():
    st.title("🏆 Classement Général")
    df = database.get_ranking_data()

    if df.empty:
        st.warning("Aucun résultat.")
        return

    # Récupération des challenges pour le filtre
    challenges = database.get_challenges()
    if not challenges:
        st.warning("Aucun challenge défini.")
        return
    ch_map = {c["id"]: c["range"] for c in challenges}

    c1, c2, c3 = st.columns(3)
    with c1:
        selected_ch_id = st.selectbox("Challenge", options=list(ch_map.keys()), format_func=lambda x: ch_map[x])
    with c2:
        choix_circuit = st.selectbox("Circuit", ["trotteur", "orienteur", "raideur"])
    with c3:
        choix_categorie = st.selectbox("Catégorie", ["Toutes", "Homme", "Femme", "Mixte"])

    # Filtrage strict par ID de challenge
    df_challenge = df[df["challenge_id"] == selected_ch_id]

    # Filtrage par circuit
    df_circuit_all = df_challenge[df_challenge["circuit"] == choix_circuit]

    # Récupération de la liste ordonnée des courses pour forcer l'affichage des colonnes
    all_courses_raw = database.get_courses_by_circuit(choix_circuit)
    challenge_courses = [c for c in all_courses_raw if c[4] == selected_ch_id]
    challenge_courses.sort(key=lambda x: x[2])  # Tri par date
    ordered_course_names = [c[1] for c in challenge_courses]
    # Mapping nom_course -> date pour affichage
    course_dates = {c[1]: format_date_fr(c[2]) for c in challenge_courses}

    if df_circuit_all.empty:
        st.info(f"Aucun résultat pour le circuit {choix_circuit} sur ce challenge.")
        return

    # Filtrage pour l'affichage (selon sélection catégorie)
    filtered_df = df_circuit_all.copy()
    if choix_categorie != "Toutes":
        filtered_df = filtered_df[filtered_df["categorie"].apply(lambda x: check_category_match(x, choix_categorie))]

    pivot = None

    # Tri chronologique
    if not filtered_df.empty:
        filtered_df = filtered_df.sort_values(by="date", ascending=True)
        
        # IMPORTANT: Classement par catégorie séparée
        # Un coureur peut être dans différentes catégories selon les étapes
        # On groupe par (nom_complet, categorie) pour créer des "identités" séparées
        
        # Créer une clé unique combinant nom et catégorie pour chaque participation
        filtered_df["coureur_categorie"] = filtered_df["nom_complet"] + " (" + filtered_df["categorie"].astype(str) + ")"
        
        # Construire le tableau: colonnes par course, valeurs = points, plus Total
        pivot = filtered_df.pivot_table(
            index=["nom_complet", "categorie"],  # Index multi-niveau
            columns="nom_course",
            values="points",
            aggfunc="sum",
            fill_value=0,
        )
        
        # Forcer les colonnes pour inclure les raids sans résultats et respecter l'ordre chronologique
        pivot = pivot.reindex(columns=ordered_course_names, fill_value=0)
        
        # Renommer les colonnes pour inclure les dates
        new_columns = {}
        for col in pivot.columns:
            if col in course_dates:
                new_columns[col] = f"{col}\n{course_dates[col]}"
            else:
                new_columns[col] = col
        pivot = pivot.rename(columns=new_columns)

        pivot["Total"] = pivot.sum(axis=1)
        pivot = pivot.sort_values(by="Total", ascending=False)
        pivot = pivot.reset_index()
        
        # Créer une colonne "Prénom Nom" qui combine nom et catégorie pour différencier
        pivot["Prénom Nom"] = pivot["nom_complet"] + " (" + pivot["categorie"] + ")"
        pivot = pivot.drop(columns=["nom_complet", "categorie"])
        pivot.insert(0, "Classement", range(1, 1 + len(pivot)))

        # Affichage du tableau récapitulatif
        titre_section = f"{choix_circuit}"
        if choix_categorie != "Toutes":
            titre_section += f" - {choix_categorie}"

        st.subheader(f"Classement - {titre_section}")
        st.dataframe(pivot, use_container_width=True, hide_index=True)
    else:
        st.info(f"Aucun résultat pour le circuit {choix_circuit} ({choix_categorie}) sur ce challenge.")
    
    # Section modification des participants
    # Afficher les messages de succès après rerun
    if st.session_state.get("participant_updated"):
        st.success("✅ Modifications enregistrées avec succès !")
        del st.session_state["participant_updated"]
    if st.session_state.get("participant_deleted"):
        st.success("🗑️ Participant supprimé avec succès !")
        del st.session_state["participant_deleted"]
    
    with st.expander("✏️ Modifier un participant"):
        if pivot is not None and not pivot.empty:
            participant_names = pivot["Prénom Nom"].tolist()
            selected_participant = st.selectbox("Sélectionner un participant", participant_names)
            
            if selected_participant:
                # Extraire le nom sans la catégorie pour la recherche
                participant_name_only = selected_participant.split(" (")[0] if " (" in selected_participant else selected_participant
                
                # Récupérer les résultats du participant
                results_df = database.get_coureur_results_for_challenge(
                    participant_name_only, selected_ch_id, choix_circuit
                )
                
                if not results_df.empty:
                    st.markdown(f"**Modification des points pour : {selected_participant}**")
                    
                    # Créer un formulaire pour modifier les points
                    with st.form(f"edit_participant_{selected_participant}"):
                        modified_points = {}
                        cols = st.columns(min(3, len(results_df)))
                        
                        for idx, (_, result) in enumerate(results_df.iterrows()):
                            col_idx = idx % 3
                            with cols[col_idx]:
                                new_points = st.number_input(
                                    f"{result['nom_course']}",
                                    min_value=0,
                                    max_value=35,
                                    value=int(result['points']),
                                    key=f"points_{result['id']}"
                                )
                                modified_points[result['id']] = {
                                    'course_id': result['course_id'],
                                    'coureur_name': selected_participant,
                                    'new_points': new_points,
                                    'old_points': result['points']
                                }
                        
                        if st.form_submit_button("✅ Sauvegarder les modifications"):
                            # Mettre à jour les points modifiés
                            changes_made = False
                            for result_id, data in modified_points.items():
                                if data['new_points'] != data['old_points']:
                                    database.update_result_points_by_id(result_id, data['new_points'])
                                    changes_made = True
                            
                            if changes_made:
                                st.session_state["participant_updated"] = True
                                st.rerun()
                            else:
                                st.info("Aucune modification détectée.")
                    
                    # Section suppression
                    st.divider()
                    st.markdown("**🗑️ Supprimer ce participant**")
                    
                    # Stocker les IDs des résultats à supprimer
                    result_ids_to_delete = [int(r['id']) for _, r in results_df.iterrows()]
                    
                    confirm_key = f"confirm_delete_participant_{participant_name_only}"
                    if st.checkbox(f"Je confirme vouloir supprimer {selected_participant} de ce circuit", key=confirm_key):
                        if st.button("🗑️ Supprimer définitivement", type="primary", key=f"delete_{participant_name_only}"):
                            for result_id in result_ids_to_delete:
                                database.delete_result_by_id(result_id)
                            st.session_state["participant_deleted"] = True
                            st.rerun()
                else:
                    st.info("Aucun résultat trouvé pour ce participant.")
        else:
            st.info("Aucun participant à modifier dans cette vue.")
    
    col_pdf_1, col_pdf_2 = st.columns(2)

    with col_pdf_1:
        if pivot is not None:
            pdf_pivot = pivot.rename(columns={"Prénom Nom": "Nom Prénom"})
            # Titre pour le PDF simple
            titre_simple = f"{choix_circuit}"
            if choix_categorie != "Toutes":
                titre_simple += f" - {choix_categorie}"
            
            pdf_input = {titre_simple: (pdf_pivot, ch_map[selected_ch_id])}
            pdf_bytes = utils.generate_pdf(pdf_input)
            st.download_button(
                "📄 Télécharger la catégorie affichée", pdf_bytes, "classement_categorie.pdf", "application/pdf"
            )
        else:
            st.write("Pas de données à télécharger pour cette vue.")

    with col_pdf_2:
        # Génération du PDF complet (Femme -> Mixte -> Homme)
        pdf_input_full = {}
        range_str = ch_map[selected_ch_id]
        
        # Ordre spécifique demandé : Femme, Mixte, Homme
        for cat in ["Femme", "Mixte", "Homme"]:
            # Filtrer sur la catégorie dans les données globales du circuit
            df_cat = df_circuit_all[df_circuit_all["categorie"].apply(lambda x: check_category_match(x, cat))]
            if not df_cat.empty:
                df_cat = df_cat.sort_values(by="date", ascending=True)
                
                # Pivot avec index multi-niveau pour gérer les participations multiples
                p_cat = df_cat.pivot_table(
                    index=["nom_complet", "categorie"],
                    columns="nom_course",
                    values="points",
                    aggfunc="sum",
                    fill_value=0,
                )
                p_cat = p_cat.reindex(columns=ordered_course_names, fill_value=0)
                
                # Renommer les colonnes pour inclure les dates dans le PDF
                new_columns_pdf = {}
                for col in p_cat.columns:
                    if col in course_dates:
                        new_columns_pdf[col] = f"{col}\n{course_dates[col]}"
                    else:
                        new_columns_pdf[col] = col
                p_cat = p_cat.rename(columns=new_columns_pdf)
                p_cat["Total"] = p_cat.sum(axis=1)
                p_cat = p_cat.sort_values(by="Total", ascending=False)
                p_cat = p_cat.reset_index()
                
                # Créer la colonne "Nom Prénom" avec catégorie pour le PDF
                p_cat["Nom Prénom"] = p_cat["nom_complet"] + " (" + p_cat["categorie"] + ")"
                p_cat = p_cat.drop(columns=["nom_complet", "categorie"])
                p_cat.insert(0, "Classement", range(1, 1 + len(p_cat)))
                
                title_cat = f"{choix_circuit} - {cat}"
                pdf_input_full[title_cat] = (p_cat, range_str)
        
        if pdf_input_full:
            pdf_bytes_full = utils.generate_pdf(pdf_input_full)
            st.download_button(
                "📄 Télécharger le circuit complet", pdf_bytes_full, "classement_complet.pdf", "application/pdf"
            )
        else:
            st.info("Pas de données pour générer le PDF complet.")


def show_edition():
    st.title("✏️ Édition des Résultats")

    # Récupération des données de base
    all_courses = database.get_all_courses()
    challenges = database.get_challenges()
    
    if not challenges:
        st.error("⚠️ Aucun challenge disponible. Veuillez d'abord créer un challenge dans l'onglet Import.")
        return
    
    ch_map = {c["id"]: c["range"] for c in challenges}

    # === SECTION 1: AJOUT DE RÉSULTAT ===
    with st.container():
        st.markdown("### ➕ Ajouter un Résultat")
        
        # Sélection du contexte
        col1, col2 = st.columns(2)
        with col1:
            selected_ch_id = st.selectbox("🏆 Saison", options=list(ch_map.keys()), format_func=lambda x: ch_map[x])
        with col2:
            # Tous les raids de la saison sélectionnée
            all_season_raids = [c for c in all_courses if c[4] == selected_ch_id]
            if not all_season_raids:
                st.warning("Aucun raid trouvé.")
                selected_raid_id = None
            else:
                raid_options = {r[0]: f"{r[1]} ({format_date_fr(r[2])}) - {r[3]}" for r in all_season_raids}
                selected_raid_id = st.selectbox("🏃 Raid", options=list(raid_options.keys()), format_func=lambda x: raid_options[x])

        # Formulaire d'ajout
        if selected_raid_id:
            with st.form("add_result_form"):
                st.markdown("#### 📝 Informations du Coureur")
                
                col_info1, col_info2, col_info3 = st.columns(3)
                with col_info1:
                    nom = st.text_input("📛 Nom")
                with col_info2:
                    prenom = st.text_input("👤 Prénom")
                with col_info3:
                    categorie = st.selectbox("🏷️ Catégorie", ["Homme", "Femme", "Mixte"])

                col_perf1, col_perf2 = st.columns(2)
                with col_perf1:
                    rang = st.number_input("🏅 Classement (catégorie)", min_value=1, value=1, key="edition_rang")
                with col_perf2:
                    # Calcul automatique des points basé sur le rang
                    points_auto = utils.calculate_points(rang)
                    st.number_input("⭐ Points (automatique)", value=points_auto, disabled=True, key="edition_points_display")
                
                if st.form_submit_button("✅ Enregistrer le résultat", use_container_width=True):
                    full_name = f"{prenom} {nom}".strip()
                    if not full_name:
                        st.error("Le nom et le prénom sont requis.")
                    else:
                        # Calcul automatique des points basé sur le rang
                        points_final = utils.calculate_points(rang)
                        
                        # Vérification de conflit
                        conflict_df = database.run_query(
                            "SELECT c.nom_complet FROM resultats r JOIN coureurs c ON r.coureur_id = c.id WHERE r.course_id = ? AND r.rang = ? AND r.categorie_course = ?",
                            (selected_raid_id, rang, categorie)
                        )
                        if not conflict_df.empty:
                            existing_name = conflict_df.iloc[0]["nom_complet"]
                            st.error(f"⚠️ Conflit : Le rang {rang} en '{categorie}' est déjà attribué à '{existing_name}'.")
                        else:
                            full_name = normalize_name(full_name)
                            coureur_id = database.add_coureur(full_name, None, None)
                            database.add_result(selected_raid_id, coureur_id, rang, int(points_final), categorie)
                            st.success(f"✅ Résultat ajouté : {full_name} - {points_final} pts")

    st.divider()

    # === SECTION 2: GESTION DES RAIDS ===
    with st.container():
        st.markdown("### 🏁 Gestion des Raids")
        
        col_manage1, col_manage2 = st.columns(2)
        with col_manage1:
            man_ch_id = st.selectbox("🏆 Saison (Gestion)", options=list(ch_map.keys()), format_func=lambda x: ch_map[x], key="man_ch_select")
        
        man_raids = [c for c in all_courses if c[4] == man_ch_id]
        man_raids.sort(key=lambda x: x[2], reverse=True)

        with col_manage2:
            if not man_raids:
                st.info("Aucun raid pour cette saison.")
                man_sel_raid_id = None
            else:
                man_raid_opts = {r[0]: f"{r[1]} ({format_date_fr(r[2])}) - {r[3]}" for r in man_raids}
                man_sel_raid_id = st.selectbox("🏃 Raid à gérer", options=list(man_raid_opts.keys()), format_func=lambda x: man_raid_opts[x], key="man_raid_select")

        if man_sel_raid_id:
            current_raid = next((r for r in man_raids if r[0] == man_sel_raid_id), None)
            if current_raid:
                st.markdown(f"#### ✏️ Modifier : **{current_raid[1]}**")
                
                with st.form("edit_raid_form"):
                    col_edit1, col_edit2 = st.columns(2)
                    with col_edit1:
                        new_name = st.text_input("🏷️ Nom du raid", value=current_raid[1])
                    with col_edit2:
                        d_val = date.today()
                        if current_raid[2]:
                            try:
                                d_val = date.fromisoformat(current_raid[2])
                            except ValueError:
                                pass
                        new_date = st.date_input("📅 Date du raid", value=d_val)
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.form_submit_button("✅ Sauvegarder", use_container_width=True):
                            if new_name and new_name != current_raid[1]:
                                database.rename_course(man_sel_raid_id, new_name)
                            if str(new_date) != current_raid[2]:
                                database.change_course_date(man_sel_raid_id, str(new_date))
                            st.success("Modifications enregistrées.")
                            st.rerun()
                    with col_btn2:
                        if st.form_submit_button("🗑️ Supprimer", type="primary", use_container_width=True):
                            # Compter le nombre de résultats qui seront supprimés
                            result_count = database.run_query(
                                "SELECT COUNT(*) as count FROM resultats WHERE course_id = ?",
                                (man_sel_raid_id,)
                            ).iloc[0]['count']
                            
                            st.warning(f"⚠️ Vous êtes sur le point de supprimer définitivement :")
                            st.error(f"• Le raid : **{current_raid[1]}**")
                            st.error(f"• Tous ses résultats : **{result_count} participants**")
                            st.error("🚫 Cette action est irréversible !")
                            
                            if st.checkbox("✅ Je confirme vouloir supprimer ce raid", key=f"confirm_delete_{man_sel_raid_id}"):
                                database.delete_course(man_sel_raid_id)
                                st.success("Raid supprimé.")
                                st.rerun()

    st.divider()

    # === SECTION 3: MAINTENANCE ===
    with st.container():
        st.markdown("### 🔧 Maintenance")
        
        with st.expander("🧹 Nettoyage des données invalides"):
            # Nettoyage des coureurs invalides
            st.markdown("**Recherche des coureurs invalides...**")
            invalid_coureurs = database.get_invalid_coureurs()
            
            if invalid_coureurs.empty:
                st.success("✅ Aucun coureur invalide trouvé.")
            else:
                st.warning(f"⚠️ {len(invalid_coureurs)} coureurs invalides détectés")
                display_df = invalid_coureurs.copy()
                display_df.columns = ["ID", "Nom", "Nb Résultats"]
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                
                total_resultats = invalid_coureurs['nb_resultats'].sum()
                st.error(f"🗑️ Suppression : {len(invalid_coureurs)} coureurs + {total_resultats} résultats")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("❌ Annuler", use_container_width=True, key="cancel_invalid"):
                        st.info("Opération annulée.")
                with col2:
                    if st.button("🗑️ Confirmer", type="primary", use_container_width=True, key="confirm_invalid"):
                        deleted_count = database.clean_invalid_coureurs()
                        st.success(f"✅ {deleted_count} coureurs supprimés.")
                        st.rerun()
            
            st.divider()
            
            # Recherche des points aberrants
            st.markdown("**Recherche des points aberrants...**")
            aberrant_points = database.get_aberrant_points()
            
            if aberrant_points.empty:
                st.success("✅ Aucun point aberrant trouvé.")
            else:
                st.warning(f"⚠️ {len(aberrant_points)} résultats avec points > 35 détectés")
                
                # Correction manuelle pour chaque résultat aberrant
                with st.form("fix_aberrant_points_form"):
                    st.markdown("**Correction manuelle des points :**")
                    corrections = {}
                    
                    for idx, row in aberrant_points.iterrows():
                        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                        
                        with col1:
                            st.write(f"**{row['nom_complet']}**")
                            st.caption(f"{row['nom_course']} - {row['categorie_course']}")
                        
                        with col2:
                            st.write(f"Rang: {row['rang']}")
                        
                        with col3:
                            st.write(f"Points actuels: **{row['points']}**")
                        
                        with col4:
                            # Points suggérés selon le rang
                            suggested_points = utils.calculate_points(row['rang'])
                            new_points = st.number_input(
                                "Nouveaux points",
                                min_value=0,
                                max_value=35,
                                value=suggested_points,
                                key=f"points_fix_{row['id']}"
                            )
                            corrections[row['id']] = {
                                'new_points': new_points,
                                'old_points': row['points']
                            }
                        
                        st.divider()
                    
                    if st.form_submit_button("🔧 Appliquer les corrections", type="primary", use_container_width=True):
                        changes_made = 0
                        for result_id, correction in corrections.items():
                            if correction['new_points'] != correction['old_points']:
                                database.update_result_points_by_id(result_id, correction['new_points'])
                                changes_made += 1
                        
                        if changes_made > 0:
                            st.success(f"✅ {changes_made} résultats corrigés.")
                            st.rerun()
                        else:
                            st.info("Aucune modification appliquée.")
            
        with st.expander("💾 Gestion des sauvegardes"):
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("💾 Créer sauvegarde maintenant", use_container_width=True):
                    backup_file = backup.create_backup()
                    if backup_file:
                        st.success(f"✅ Sauvegarde créée : {os.path.basename(backup_file)}")
                    else:
                        st.error("❌ Erreur lors de la sauvegarde")
            
            with col2:
                if st.button("🗑️ Nettoyer anciennes sauvegardes", use_container_width=True):
                    backup.cleanup_old_backups(7)  # Garder 7 jours
                    st.success("✅ Nettoyage effectué")
            
            # Affichage des sauvegardes existantes
            backups = backup.get_backup_status()
            if backups:
                st.markdown("**Sauvegardes disponibles :**")
                for b in backups:
                    st.text(f"• {b['filename']} - {b['date']} ({b['size']})")
            else:
                st.info("Aucune sauvegarde trouvée")

    st.divider()

    # === SECTION 4: HISTORIQUE DES MODIFICATIONS ===
    with st.container():
        st.markdown("### 📝 Historique des modifications")
        
        # Initialiser l'audit log si nécessaire
        audit.init_audit_log()
        
        tab1, tab2 = st.tabs(["Modifications récentes", "Changements de points"])
        
        with tab1:
            recent_mods = audit.get_recent_modifications()
            
            if not recent_mods.empty:
                # Formatage pour affichage
                display_mods = recent_mods.copy()
                display_mods['timestamp'] = pd.to_datetime(display_mods['timestamp']).dt.strftime('%d/%m/%Y %H:%M')
                st.dataframe(display_mods[['timestamp', 'action', 'table_name']], use_container_width=True, hide_index=True)
            else:
                st.info("Aucune modification enregistrée")
        
        with tab2:
            point_mods = audit.get_point_modifications()
            
            if not point_mods.empty:
                st.markdown("**Dernières modifications de points :**")
                for _, mod in point_mods.iterrows():
                    timestamp = pd.to_datetime(mod['timestamp']).strftime('%d/%m/%Y %H:%M')
                    st.text(f"• {timestamp} - Résultat ID {mod['record_id']} modifié")
            else:
                st.info("Aucune modification de points enregistrée")

if __name__ == "__main__":
    main()
