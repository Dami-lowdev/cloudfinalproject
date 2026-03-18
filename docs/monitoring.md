# Monitoring — Content Platform
 
 ## Azure Monitor
 
 - **Workspace** : law-content-platform (norwayeast)
 - **Retention** : 30 jours
 - **Niveau de logs** : INFO
 
 ## Metriques surveillees
 
 | Metrique | Seuil d'alerte | Action |
 |---|---|---|
 | CPU noeud | > 80% | Alerte email |
 | RAM pods | > 200 Mi | Verification manuelle |
 | Pods disponibles | < 2 | Alerte critique |
 
 ## Commandes utiles
 
 ```bash
# Metriques en temps reel
 kubectl top pods -n content-platform
 kubectl top nodes
 
 # Logs applicatifs
 kubectl logs -l app=content-platform -n content-platform --tail=100 -f
 ```

