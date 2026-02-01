import streamlit as st
import pandas as pd
import database
import audit
from datetime import datetime, timedelta

def show_dashboard():
    st.title("📊 Tableau de Bord")
    
    # Vue d'ensemble
    show_overview()
    
    st.divider()
    
    # Statistiques par circuit
    show_circuit_stats()
    
    st.divider()
    
    # Statistiques détaillées
    show_detailed_stats()
    
    st.divider()
    
    # Historique des modifications
    show_modification_history()

def show_overview():
    st.subheader("🎯 Vue d'ensemble")
    
    # Statistiques générales
    total_raids = database.run_query("SELECT COUNT(*) as count FROM courses").iloc[0]['count']
    total_participants = database.run_query("SELECT COUNT(DISTINCT coureur_id) as count FROM resultats").iloc[0]['count']
    total_results = database.run_query("SELECT COUNT(*) as count FROM resultats").iloc[0]['count']
    
    # Dernière activité
    last_activity = database.run_query("""
        SELECT MAX(date) as last_date, nom_course 
        FROM courses 
        WHERE date = (SELECT MAX(date) FROM courses)
    """)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🏁 Total Raids", total_raids)
    
    with col2:
        st.metric("👥 Participants uniques", total_participants)
    
    with col3:
        st.metric("📈 Total résultats", total_results)
    
    with col4:
        if not last_activity.empty:
            last_date = last_activity.iloc[0]['last_date']
            st.metric("📅 Dernier raid", last_date)
        else:
            st.metric("📅 Dernier raid", "Aucun")

def show_circuit_stats():
    st.subheader("📋 Participation par circuit")
    
    # Participation par circuit
    circuit_data = database.run_query("""
        SELECT circuit, COUNT(*) as nb_raids, COUNT(DISTINCT coureur_id) as nb_participants
        FROM courses c
        JOIN resultats r ON c.id = r.course_id
        GROUP BY circuit
        ORDER BY circuit
    """)
    
    if not circuit_data.empty:
        st.dataframe(circuit_data, use_container_width=True)
        
        # Graphique simple avec barres
        st.bar_chart(circuit_data.set_index('circuit')[['nb_raids', 'nb_participants']])
    else:
        st.info("Aucune donnée de participation disponible")

def show_detailed_stats():
    st.subheader("📋 Statistiques détaillées")
    
    tab1, tab2, tab3 = st.tabs(["Par raid/catégorie", "Taux de participation", "Top participants"])
    
    with tab1:
        # Participants par raid et catégorie
        raid_stats = database.run_query("""
            SELECT c.nom_course, c.date, c.circuit, r.categorie_course,
                   COUNT(*) as nb_participants
            FROM courses c
            JOIN resultats r ON c.id = r.course_id
            GROUP BY c.id, r.categorie_course
            ORDER BY c.date DESC, c.nom_course, r.categorie_course
        """)
        
        if not raid_stats.empty:
            st.dataframe(raid_stats, use_container_width=True)
        else:
            st.info("Aucune statistique de raid disponible")
    
    with tab2:
        # Taux de participation par coureur
        participation_rate = database.run_query("""
            SELECT c.nom_complet,
                   COUNT(*) as nb_participations,
                   COUNT(DISTINCT co.circuit) as nb_circuits,
                   ROUND(AVG(r.points), 1) as points_moyens
            FROM coureurs c
            JOIN resultats r ON c.id = r.coureur_id
            JOIN courses co ON r.course_id = co.id
            GROUP BY c.id
            ORDER BY nb_participations DESC
            LIMIT 20
        """)
        
        if not participation_rate.empty:
            st.dataframe(participation_rate, use_container_width=True)
        else:
            st.info("Aucune donnée de participation disponible")
    
    with tab3:
        # Top participants par points
        top_participants = database.run_query("""
            SELECT c.nom_complet,
                   SUM(r.points) as total_points,
                   COUNT(*) as nb_raids,
                   ROUND(AVG(r.points), 1) as moyenne_points
            FROM coureurs c
            JOIN resultats r ON c.id = r.coureur_id
            GROUP BY c.id
            ORDER BY total_points DESC
            LIMIT 15
        """)
        
        if not top_participants.empty:
            st.dataframe(top_participants, use_container_width=True)
        else:
            st.info("Aucun participant trouvé")

def show_modification_history():
    st.subheader("📝 Historique des modifications")
    
    # Initialiser l'audit log si nécessaire
    audit.init_audit_log()
    
    tab1, tab2 = st.tabs(["Modifications récentes", "Changements de points"])
    
    with tab1:
        recent_mods = audit.get_recent_modifications()
        
        if not recent_mods.empty:
            # Formatage pour affichage
            display_mods = recent_mods.copy()
            display_mods['timestamp'] = pd.to_datetime(display_mods['timestamp']).dt.strftime('%d/%m/%Y %H:%M')
            st.dataframe(display_mods[['timestamp', 'action', 'table_name']], use_container_width=True)
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
        
        # Bouton pour annuler les dernières actions (placeholder)
        if st.button("🔄 Annuler dernière modification", disabled=True):
            st.warning("Fonctionnalité en développement")