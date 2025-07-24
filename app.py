import streamlit as st
import pandas as pd
from db import init_db, get_connection

init_db()
st.title("📦 Inventaire - La Charpenterie")

menu = st.sidebar.selectbox("Navigation", [
    "Ajouter un matériau", "Modifier un matériau", "Supprimer un matériau",
    "Stock actuel", "Entrée / Sortie", "Exporter Excel"
])

conn = get_connection()
c = conn.cursor()

def charger_types():
    return [r[0] for r in c.execute("SELECT nom FROM types").fetchall()]

def charger_zones():
    return [r[0] for r in c.execute("SELECT nom FROM zones").fetchall()]

def get_type_id(nom):
    c.execute("SELECT id FROM types WHERE nom=?", (nom,))
    return c.fetchone()[0]

def get_zone_id(nom):
    c.execute("SELECT id FROM zones WHERE nom=?", (nom,))
    return c.fetchone()[0]

if menu == "Ajouter un matériau":
    st.header("➕ Nouveau matériau")

    types = sorted([t for t in charger_types() if t.strip()])
    type_sel = st.selectbox("Type", types + ["➕ Nouveau type"])

    if type_sel == "➕ Nouveau type":
        nv_type = st.text_input("Nouveau type")
        if st.button("Ajouter type"):
            c.execute("INSERT INTO types (nom) VALUES (?)", (nv_type,))
            conn.commit()
            st.success("Type ajouté.")
            st.rerun()

    dimensions = ""
    ref = ""
    nom = ""

    essences = {
        "Épicéa brut": "S", "KVH épicéa": "SKVH", "Douglas brut": "D", "Douglas KVH": "DKVH",
        "Cl4 brut": "Cl4b", "Cl4 raboté": "Cl4rbt", "Chêne": "Che", "Châtaigner": "Cha",
        "Lamibois": "Lmb", "Poutre I": "I", "LC épicéa": "LCS", "LC douglas": "LCD",
        "LC cl3": "LCCl3", "LC cl4": "LCCl4", "Contre collé épicéa": "CCS", "Contre collé douglas": "CCD"
    }

    if type_sel.lower() == "bois":
        essence_nom = st.selectbox("Essence", list(essences.keys()))
        essence_code = essences[essence_nom]

        hauteur = st.number_input("Hauteur (mm)", min_value=10, step=10)
        largeur = st.number_input("Largeur (mm)", min_value=10, step=10)
        longueur = st.number_input("Longueur (m)", min_value=0.1, step=0.1)

        dimensions = f"{int(hauteur)}x{int(largeur)}x{int(longueur * 1000)}"
        ref = f"{essence_code}_{dimensions}"
        st.text_input("Référence générée", ref, disabled=True)

        nom = st.text_input("Nom (facultatif)", f"{essence_nom} {dimensions}")
    else:
        nom = st.text_input("Nom")
        ref = st.text_input("Référence")
        dimensions = st.text_input("Dimensions (ex: 45x145x4000)")

    qte = st.number_input("Quantité", min_value=0, step=1)
    prix = st.number_input("Prix (optionnel)", min_value=0.0, format="%.2f")
    commentaire = st.text_area("Commentaire")

    zones = sorted([z for z in charger_zones() if z.strip()])
    zone_sel = st.selectbox("Zone", zones + ["➕ Nouvelle zone"])

    if zone_sel == "➕ Nouvelle zone":
        nv_zone = st.text_input("Nouvelle zone")
        if st.button("Ajouter zone"):
            c.execute("INSERT INTO zones (nom) VALUES (?)", (nv_zone,))
            conn.commit()
            st.success("Zone ajoutée.")
            st.rerun()

    if st.button("Ajouter au stock"):
        id_type = get_type_id(type_sel)
        id_zone = get_zone_id(zone_sel)
        c.execute('''INSERT INTO materiaux (nom, ref, type_id, zone_id, dimensions, qte, prix, commentaire)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                  (nom, ref, id_type, id_zone, dimensions, qte, prix, commentaire))
        conn.commit()
        st.success("Matériau ajouté.")


elif menu == "Modifier un matériau":
    st.header("✏️ Modifier un matériau existant")
    noms = [r[0] for r in c.execute("SELECT nom FROM materiaux").fetchall()]
    nom_sel = st.selectbox("Sélectionner un matériau", noms)

    if nom_sel:
        c.execute('''SELECT m.ref, t.nom, z.nom, m.dimensions, m.qte, m.prix, m.commentaire
                     FROM materiaux m
                     JOIN types t ON m.type_id = t.id
                     JOIN zones z ON m.zone_id = z.id
                     WHERE m.nom = ?''', (nom_sel,))
        data = c.fetchone()

        ref, type_actuel, zone_actuelle, dim, qte, prix, com = data

        nv_ref = st.text_input("Référence", ref)
        nv_dim = st.text_input("Dimensions", dim)
        nv_qte = st.number_input("Quantité", min_value=0, value=qte)
        nv_prix = st.number_input("Prix", min_value=0.0, value=prix, step=0.01)
        nv_com = st.text_area("Commentaire", com)

        types = charger_types()
        zones = charger_zones()

        nv_type = st.selectbox("Type", types, index=types.index(type_actuel))
        nv_zone = st.selectbox("Zone", zones, index=zones.index(zone_actuelle))

        if st.button("Enregistrer les modifications"):
            type_id = get_type_id(nv_type)
            zone_id = get_zone_id(nv_zone)
            c.execute('''UPDATE materiaux
                         SET ref=?, type_id=?, zone_id=?, dimensions=?, qte=?, prix=?, commentaire=?
                         WHERE nom=?''',
                      (nv_ref, type_id, zone_id, nv_dim, nv_qte, nv_prix, nv_com, nom_sel))
            conn.commit()
            st.success("Matériau mis à jour.")
            st.rerun()

elif menu == "Supprimer un matériau":
    st.header("🗑️ Supprimer un matériau")
    noms = [r[0] for r in c.execute("SELECT nom FROM materiaux").fetchall()]
    nom_sel = st.selectbox("Sélectionner le matériau à supprimer", noms)

    if nom_sel:
        c.execute("SELECT ref, qte, zone_id FROM materiaux WHERE nom=?", (nom_sel,))
        ref, qte, zone_id = c.fetchone()
        st.write(f"Référence : {ref}")
        st.write(f"Quantité : {qte}")
        zone_nom = c.execute("SELECT nom FROM zones WHERE id=?", (zone_id,)).fetchone()[0]
        st.write(f"Zone : {zone_nom}")
        confirm = st.checkbox("Je confirme la suppression définitive de ce matériau")
        if confirm:
            if st.button("Supprimer"):
                c.execute("DELETE FROM materiaux WHERE nom=?", (nom_sel,))
                conn.commit()
                st.success("Matériau supprimé.")
                st.rerun()

elif menu == "Stock actuel":
    st.header("📋 Stock actuel")

    df = pd.read_sql_query('''
        SELECT m.id, m.nom, m.ref, t.nom AS type, z.nom AS zone,
               m.dimensions, m.qte, m.prix, m.commentaire
        FROM materiaux m
        JOIN types t ON m.type_id = t.id
        JOIN zones z ON m.zone_id = z.id
    ''', conn)

    df["coût_total"] = df["qte"] * df["prix"]
    df["coût_total"] = df["coût_total"].round(2)

    st.subheader("🔍 Filtres")
    types_dispo = sorted(df["type"].unique())
    zones_dispo = sorted(df["zone"].unique())

    filtre_type = st.multiselect("Type", types_dispo, default=types_dispo)
    filtre_zone = st.multiselect("Zone", zones_dispo, default=zones_dispo)
    filtre_texte = st.text_input("Filtrer par nom ou référence")

    df_filtré = df[
        df["type"].isin(filtre_type) &
        df["zone"].isin(filtre_zone)
    ]

    if filtre_texte:
        filtre_texte = filtre_texte.lower()
        df_filtré = df_filtré[
            df_filtré["nom"].str.lower().str.contains(filtre_texte) |
            df_filtré["ref"].str.lower().str.contains(filtre_texte)
        ]

    st.dataframe(df_filtré)

elif menu == "Entrée / Sortie":
    st.header("🔄 Ajuster les quantités")
    noms = [r[0] for r in c.execute("SELECT nom FROM materiaux")]
    mat_nom = st.selectbox("Matériau", noms)
    c.execute("SELECT qte FROM materiaux WHERE nom=?", (mat_nom,))
    qte_actuelle = c.fetchone()[0]
    st.write(f"Quantité actuelle : **{qte_actuelle}**")

    entree = st.number_input("Entrée", min_value=0, step=1)
    sortie = st.number_input("Sortie", min_value=0, step=1)

    if st.button("Valider"):
        nouvelle_qte = qte_actuelle + entree - sortie
        c.execute("UPDATE materiaux SET qte=? WHERE nom=?", (nouvelle_qte, mat_nom))
        conn.commit()
        st.success(f"Quantité mise à jour : {nouvelle_qte}")
        st.rerun()

elif menu == "Exporter Excel":
    st.header("📤 Export Excel")
    df = pd.read_sql_query('''
        SELECT m.nom, m.ref, t.nom AS type, z.nom AS zone,
               m.dimensions, m.qte, m.prix, m.commentaire
        FROM materiaux m
        JOIN types t ON m.type_id = t.id
        JOIN zones z ON m.zone_id = z.id
    ''', conn)

    df["coût_total"] = df["qte"] * df["prix"]
    df["coût_total"] = df["coût_total"].round(2)

    st.download_button("Télécharger le stock", data=df.to_excel(index=False, engine="openpyxl"),
                       file_name="stock_charpenterie.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
