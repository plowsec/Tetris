# -*- coding: utf-8 -*-


from PyQt4.QtCore import *
from PyQt4.QtGui import *

import random
from time import time
import sys
import sqlite3
from datetime import datetime

class Jeu(object):
    """Définition de la fenêtre principale de jeu"""

    def __init__(self):
        self.isPaused = False
        self.isStarted = False
        self.pseudo = ""
        self.level = 9
        self.board = Tetris(self)
        self.board.show()
        self.createBDD()
        self.flagKeyDown = False
        self.bonus = 0

    def createBDD(self):
        """ Création d'une base de données avec nom, prénom,
        pseudo, mot de passe, confirmation du mot de passe"""

        conn = sqlite3.connect("BDDTetris.sq3")
        cur = conn.cursor()
        try:
            requete = """CREATE TABLE Joueur(JoueurID INTEGER PRIMARY KEY AUTOINCREMENT,
            Nom varchar(40) NOT NULL, Prenom varchar(40) NOT NULL, Pseudo varchar(40) NOT NULL,
            MotDePasse varchar(20));"""
            cur.execute(requete)
            requete2 = """CREATE TABLE HighScores(Pseudo VARCHAR(40), Score INT NOT NULL,
            LignesCompletees INT NOT NULL, date Date NOT NULL,
            FOREIGN KEY(Pseudo) REFERENCES Joueur(Pseudo));"""
            cur.execute(requete2)

        except:
            pass
        conn.commit()
        cur.close()
        conn.close()

    def start(self):
        """ Fonction permettant de lancer le jeu"""
        self.timer = QTimer()
        self.board.actionStop.setEnabled(True)
        self.points = 0
        self.lignesCompletees=0
        self.isGameOver = False
        self.piece = Piece(self.board, 1)
        self.nextPiece = Piece(self.board)
        self.board.labelNext.setPixmap(QPixmap("Sprites/"+self.nextPiece.noms[self.nextPiece.index]+".png"))
        self.board.updateBoard()
        self.timer.start(1000 / (1 + self.level))
        self.timer.timeout.connect(self.chute)

    def pause(self):
        """ Fonction permettant d'activer/désactiver la pause
        du jeu et d'ouvrir une fenetre de dialogue"""

        if self.isPaused == True:
            self.isPaused = False
        else:
            self.isPaused = True

        if self.isPaused == True:
            self.timer.stop()
            pause = DialogPause(self)
            pause.exec()
        else:
            self.piece.setLastChange()
            self.timer.start(1000 / (1 + self.level))

    def gameOver(self): #pour des raisons de logique, on contrôle si la pièce a la place pour spawn dans la classe Piece, si elle n'a pas la place, on appelle gameOver()
        """Fonction permettant de mettre fin au jeu
        et d'ouvrir une fenêtre de dialogue"""
        self.board.actionStop.setEnabled(False)
        self.timer.stop()
        self.board.labelInfos.setText("Vous avez perdu! \n")
        self.saveScore()
        self.isGameOver = True
        self.board.actionNewGame.setEnabled(True)
        nouveau = DialogNew(self)
        nouveau.exec()

    def saveScore(self):
        """ Fonction permettant d'enregistrer
        le score dans la base de données"""

        conn = sqlite3.connect("BDDTetris.sq3")
        cur = conn.cursor()
        now = datetime.now().date()

        cur.execute("""INSERT INTO HighScores(Pseudo, Score, LignesCompletees, Date) VALUES(?,?,?,?)""",(self.pseudo, self.points, self.lignesCompletees, now))
        conn.commit()
        cur.close()
        conn.close()

    def newGame(self):
        """ Fonction permettant de vérifier que l'utilisateur
        soit inscrit avant de commencer à jouer"""

        if self.pseudo == "":
            self.login()
        if self.pseudo =="":
            return
        self.board.actionNewGame.setEnabled(False)
        self.board.boutonJouer.setEnabled(False)
        self.start()

    def login(self): #On ne peut pas la mettre directement dans newGame ???
        """ Fonction permettant d'ouvrir la fenetre de
        dialogue pour l'inscription"""

        dialog = DialogLogin(self)
        dialog.exec()
        self.board.actionLogin.setEnabled(False)

    def aide(self):
        """ Fonction permettant d'ouvrir la fenetre de
        dialogue pour l'aide à l'utilisateur"""

        aide = DialogHelp(self)
        aide.exec()

    def ligneComplete(self): #détecte si une ligne est complète
        """Fonction permettant de détecter si une/des ligne(s)
        du jeu est/sont complète et l/les efface"""

        self.nbrLignes = 0
        for j in range(20):
            i,nbrCarres = 0,0
            while i<10:
                if self.board.grille[i][j]!=0:
                    nbrCarres+=1
                i+=1
            if nbrCarres == 10:
                self.nbrLignes+=1
                for n in range(10):
                    self.board.grille[n][j]=0
                self.toutLeMondeDescend(j)
        if self.nbrLignes >0: #Lorsqu'une ou plusieurs lignes sont repérée(s) on appelle la fonction score
            self.score()
            return True

    def toutLeMondeDescend(self,j):
        """ Fonction permettant de faire descendre les lignes incomplètes
        se situant au dessus de la (des) ligne(s) complétée(s)"""

        i=0
        while j > 5:
            i = 0
            while i < 10:
                self.board.grille[i][j] = self.board.grille[i][j-1]
                i+=1
            j-=1
        self.board.cleanBoard()

    def hardDrop(self): #A optimiser!#j'ai trouvé plus simple, on la garde comme souvenir
        """ Fonction permettant de faire chuter la pièce
        en jeu au point le plus bas possible"""

        x1 = self.piece.getMinH()
        x2 = self.piece.getMaxH()
        y = self.piece.getMaxV()
        for j in range(y+1,20):
            nbCasesLibres=0
            for i in range(x1,x2+1):
                if self.board.grille[j][i]==0:
                    nbCasesLibres+=1
                else:
                    return j-1
        return 19

    def score(self): #A optimier!
        """ Fonction permettant de gérer le score"""

        if self.nbrLignes == 1:
            self.points += 40
        elif self.nbrLignes == 2:
            self.points += 100
        elif self.nbrLignes == 3:
            self.points += 300
        elif self.nbrLignes == 4:
            self.points += 1200
        self.lignesCompletees+=self.nbrLignes
        self.board.lcdLignes.display(self.lignesCompletees)
        self.board.lcdScore.display(self.points)
        return 19

    def chute(self):
        """ Fonction permettant de faire chuter la pièce et,
        une fois posée, de relancer le processus"""
        if self.isGameOver == True:
            return
        if self.piece.estPosee()==True:
            self.points+=self.level+1
            self.board.lcdScore.display(self.points)
            for i in range(4):
                self.board.grille[self.piece.coords[i][0]][self.piece.coords[i][1]]=self.piece.index+1
            self.ligneComplete()
            self.board.updateBoard()
            self.piece = self.nextPiece
            self.piece.create()
            self.nextPiece = Piece(self.board)
            self.board.labelNext.setPixmap(QPixmap("Sprites/"+self.nextPiece.noms[self.nextPiece.index]+".png"))
            self.piece.setLastChange()
            return
        if self.piece.checkCollisions(0,1) != True:
            self.piece.move(0,1)
            self.piece.setLastChange()
    def specialHardDrop(self):
        while self.piece.checkCollisions(0,1)!=True:
            self.bonus+=1
            self.piece.move(0,1)
        self.points+=self.bonus
        self.bonus =0
    def keepMoving(self):
        if self.flagKeyDown == True:
            if self.piece.checkCollisions(0,1) != True:
                self.piece.move(0,1)
                self.bonus+=1
                self.timer.start(100)
                self.timer.timeout.connect(self.keepMoving)
            else:
                self.flagKeyDown = False
                self.points+=self.bonus
                self.bonus =0

    def myKeyReleaseEvent(self, event):
        if event.key()==Qt.Key_S:
            self.flagKeyDown = False
            self.points+=self.bonus
            self.bonus =0
    def myKeyPressEvent(self,event):
        """ Fonction permettant de déterminer l'action
        de chacune des touches du jeu"""
        if event.key()==Qt.Key_S:
            self.flagKeyDown = True
            self.keepMoving()
        elif event.key() == Qt.Key_A:
            if self.piece.checkCollisions(-1,0) != True:
                self.piece.move(-1,0)
        elif event.key() == Qt.Key_D:
            if self.piece.checkCollisions(1,0) != True:
                self.piece.move(1,0)
        elif event.key() == Qt.Key_W:
            self.piece.tourne()
        elif event.key() == Qt.Key_P:
            self.pause()
        elif event.key()==Qt.Key_Space:
           # self.piece.move(0,self.hardDrop())
            self.specialHardDrop()
class Tetris(QMainWindow):
    def __init__(self,master):
        super(Tetris, self).__init__()
        self.LARGEUR = 9
        self.HAUTEUR = 19
        self.master = master
        #initialisation de la fen�tre et de ses composants

        self.setFixedSize(725,685)
        self.setWindowTitle("Rytz Industries Tetris")
        self.setWindowIcon(QIcon("Sprites/icone.png"))
        self.scene = QGraphicsScene(self)
        self.vue = QGraphicsView(self.scene, self)
        self.vue.setRenderHints(QPainter.Antialiasing|QPainter.TextAntialiasing)
        self.vue.setGeometry(32,32,320,640)
        self.vue.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff);
        self.vue.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff);
        self.board = self.scene.addPixmap(QPixmap("Sprites/Wallpaper.jpg"))
        self.board.setPos(32,32)
        self.setStyleSheet("QMainWindow {background-image: url(Sprites/dark-metal-texture.jpg); }")

        self.labelNext = QLabel(self)
        self.labelNext.setGeometry(384,32,150,150)
        self.labelNext.setStyleSheet("border: 1px solid  white ;")
        self.labelNext.setPixmap(QPixmap("Sprites/accueil.jpg"))

        self.labelNiveau = QLabel(self)
        self.createLabel(self.labelNiveau, "Niveau : ")
        self.labelNiveau.setGeometry(384,200,150,50)

        self.labelLignes = QLabel(self)
        self.createLabel(self.labelLignes, "Lignes : ")
        self.labelLignes.setGeometry(384,300,150,50)

        self.labelScore = QLabel(self)
        self.createLabel(self.labelScore, "Score : ")
        self.labelScore.setGeometry(384,400,150,50)

        self.lcdNiveau = QLCDNumber(self)
        self.createLCDNumber(self.lcdNiveau)
        self.lcdNiveau.setGeometry(384,250,150,50)
        self.lcdNiveau.display(self.master.level)

        self.lcdLignes = QLCDNumber(self)
        self.createLCDNumber(self.lcdLignes)
        self.lcdLignes.setGeometry(384,350,150,50)

        self.lcdScore = QLCDNumber(self)
        self.createLCDNumber(self.lcdScore)
        self.lcdScore.setGeometry(384,450,150,50)

        self.labelInfos = QLabel(self)
        self.createLabel(self.labelInfos, "Bonjour, visiteur...\nEntre ton login\npour jouer une partie.", 17)
        self.labelInfos.setGeometry(384, 520,450,100)

        self.boutonJouer = QPushButton("Jouer", self)
        self.boutonJouer.setGeometry(384, 620, 150,52)
        self.boutonJouer.setStyleSheet("font-size: 18pt;font-weight: bold;")
        self.boutonJouer.clicked.connect(self.master.newGame)

        #Barre de menu
        self.menuBar = self.menuBar()
        self.menuFichier = self.menuBar.addMenu("&Fichier")
        self.actionNewGame = self.menuFichier.addAction("Nouvelle partie")
        self.actionNewGame.setShortcut(QKeySequence("F2"))
        self.actionNewGame.triggered.connect(self.master.newGame)
        self.actionLogin = self.menuFichier.addAction("Se logger")
        self.actionLogin.triggered.connect(self.master.login)
        self.actionScores = self.menuFichier.addAction("&Highscores...")
        self.actionScores.triggered.connect(self.afficherScores)
        self.actionStop = self.menuFichier.addAction("&Quitter la partie")
        self.actionStop.triggered.connect(self.master.gameOver)
        self.actionStop.setEnabled(False)
        self.actionQuitter = self.menuFichier.addAction("&Quitter")
        self.actionQuitter.setShortcut(QKeySequence("Ctrl+Q"))
        self.actionQuitter.triggered.connect(qApp.quit)

        self.menuOption = self.menuBar.addMenu("&Options")
        self.actionTextures = self.menuOption.addAction("&Changer les textures...")

        self.menuAide = self.menuBar.addMenu("&?")
        self.actionAPropos = self.menuAide.addAction("A propos...")
        self.actionAide = self.menuAide.addAction("&Aide")
        self.actionAide.setShortcut(QKeySequence("F1"))
        self.actionAide.triggered.connect(self.master.aide)

        #initialisation de deux grilles : l'une, abstraite, traitant du positionnement des items, et l'autre permettant d'afficher le contenu du tableau de jeu.
        self.grille = []
        for i in range(10):
            self.grille.append([])
            for j in range(20):
                self.grille[i].append(0)

        self.grilleImages = []
        self.imagesPiece = []
        for i in range(4):
            item = QGraphicsItem
            self.imagesPiece.append(item)
        self.updateBoard()
    def clearGrille(self):
        self.grille = []
        for i in range(10):
            self.grille.append([])
            for j in range(20):
                self.grille[i].append(0)

        self.grilleImages = []
        self.imagesPiece = []
        for i in range(4):
            item = QGraphicsItem
            self.imagesPiece.append(item)
    def createLabel(self,label, text, size=25):
        label.setText(text)
        f=QFont( "Arial", size, QFont.Bold);
        pal = QPalette(label.palette())
        pal.setColor(QPalette.WindowText, QColor(Qt.white))
        label.setPalette(pal)
        label.setFont(f)
    def createLCDNumber(self, lcd):
        lcd.setStyleSheet("background-color: white")
        lcd.setSegmentStyle(QLCDNumber.Filled);
    def prout(self):
        print("{")
        for i in range(10):
            print("{")
            for j in range(20):
                print(self.grille[i][j],end=",")
            print("}\n")
    def cleanBoard(self):
        self.scene.clear()
        self.scene.addPixmap(QPixmap("Sprites/dark-metal-texture.jpg"))
        self.board = self.scene.addPixmap(QPixmap("Sprites/Wallpaper.jpg"))
        self.board.setPos(32,32)
    def updateBoard(self):
        for i in range(10):
            for j in range(20):
                if self.grille[i][j]==0:
                    continue
                elif self.grille[i][j]==1:
                    self.grilleImages.append(self.scene.addPixmap(QPixmap(self.master.piece.carres[0])))
                elif self.grille[i][j]==2:
                    self.grilleImages.append(self.scene.addPixmap(QPixmap(self.master.piece.carres[1])))
                elif self.grille[i][j]==3:
                    self.grilleImages.append(self.scene.addPixmap(QPixmap(self.master.piece.carres[2])))
                elif self.grille[i][j]==4:
                    self.grilleImages.append(self.scene.addPixmap(QPixmap(self.master.piece.carres[3])))
                elif self.grille[i][j]==5:
                    self.grilleImages.append(self.scene.addPixmap(QPixmap(self.master.piece.carres[4])))
                elif self.grille[i][j]==6:
                    self.grilleImages.append(self.scene.addPixmap(QPixmap(self.master.piece.carres[5])))
                elif self.grille[i][j]==7:
                    self.grilleImages.append(self.scene.addPixmap(QPixmap(self.master.piece.carres[6])))
                try:
                    self.grilleImages[len(self.grilleImages)-1].setPos((i+1)*32,(j+1)*32)
                except IndexError:
                    continue
                else:
                    continue
    def keyPressEvent(self,event):
        self.master.myKeyPressEvent(event)
    def keyReleaseEvent(self, event):
        self.master.myKeyReleaseEvent(event)
    def afficherScores(self):
        dialog = DialogScore(self)
        dialog.exec()
class DialogPause(QDialog): #Fais apparaitre une fenetre lorsque le jeu est en pause
    def __init__(self, parent):
        self.parent = parent
        super(DialogPause, self).__init__()
        tabWidget=QTabWidget()
        layoutPrincipal = QVBoxLayout()
        regles = QWidget()
        labelRegles = QLabel("Le jeu a été mis en pause")
        layoutRegles = QVBoxLayout()
        layoutRegles.addWidget(labelRegles)
        regles.setLayout(layoutRegles)
        tabWidget.addTab(regles, "Menu de pause")
        bouton = QPushButton("Fermer")
        bouton.clicked.connect(self.retour)
        layoutPrincipal.addWidget(tabWidget)
        layoutPrincipal.addWidget(bouton)
        self.setLayout(layoutPrincipal)
    def retour(self):
        self.parent.isOver=False
        self.parent.pause()
        self.close()
class DialogNew(QDialog): #Fais apparaitre une fenetre lorsque le jeu est terminé
    def __init__(self, parent):
        self.parent = parent
        super(DialogNew, self).__init__()
        tabWidget=QTabWidget()
        layoutPrincipal = QVBoxLayout()
        regles = QWidget()
        labelRegles = QLabel("Tu as perdu")
        layoutRegles = QVBoxLayout()
        layoutRegles.addWidget(labelRegles)
        regles.setLayout(layoutRegles)
        tabWidget.addTab(regles, "Fin de partie")
        bouton = QPushButton("Fermer")
        bouton.clicked.connect(self.close)
        bouton2 = QPushButton("Nouvelle partie")
        bouton2.clicked.connect(self.nouvPartie)
        layoutPrincipal.addWidget(tabWidget)
        layoutPrincipal.addWidget(bouton)
        layoutPrincipal.addWidget(bouton2)
        self.setLayout(layoutPrincipal)
    def nouvPartie(self):
        self.parent.board.cleanBoard()
        self.parent.board.clearGrille()
        self.parent.board.lcdScore.display(0)
        self.parent.board.lcdLignes.display(0)
        #self.parent.board.updateBoard()
        self.parent.start()
        self.close()
class DialogScore(QDialog):
    def __init__(self, parent):
        self.parent = parent
        super(DialogScore, self).__init__()
        self.setWindowTitle("HighScores")
        self.setWindowIcon(QIcon("Sprites/icone.png"))
        self.resize(300,400)
        tabWidget = QTabWidget()
        bouton = QPushButton("Fermer")
        bouton.clicked.connect(self.close)
        layoutPrincipal = QVBoxLayout()

        highScores = QWidget()
        personalScores = QWidget()

        self.grilleLabel=[]
        layoutGrille = QGridLayout()
        for i in range(11):
            self.grilleLabel.append([])
            for j in range(5):
                self.grilleLabel[i].append(QLabel())
                layoutGrille.addWidget(self.grilleLabel[i][j],i,j)


        self.grilleLabel2=[]
        layoutGrille2 = QGridLayout()
        for i in range(11):
            self.grilleLabel2.append([])
            for j in range(5):
                self.grilleLabel2[i].append(QLabel())
                layoutGrille2.addWidget(self.grilleLabel2[i][j],i,j)
        titres_colonnes = ["Rang", "Pseudo", "Score", "Lignes", "Date"]
        for c in range(5):
            self.grilleLabel[0][c].setText("<u><b>"+titres_colonnes[c]+"</u></b>")
            self.grilleLabel2[0][c].setText("<u><b>"+titres_colonnes[c]+"</u></b>")


        highScores.setLayout(layoutGrille)
        personalScores.setLayout(layoutGrille2)
        tabWidget.addTab(highScores, "Meilleurs scores")
        tabWidget.addTab(personalScores, "Vos scores")

        layoutPrincipal.addWidget(tabWidget)
        layoutPrincipal.addWidget(bouton)
        self.setLayout(layoutPrincipal)

        if self.parent.master.pseudo=="":
            personalScores.setEnabled(False)
        self.fillWithData()
    def fillWithData(self):
        conn = sqlite3.connect("BDDTetris.sq3")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        requete = """SELECT * FROM HighScores ORDER BY Score DESC"""
        cur.execute(requete)
        lignes = cur.fetchall()
        i=1
        for l in lignes:
            if i < 11:
                self.grilleLabel[i][0].setText(str(i))
                self.grilleLabel[i][1].setText(l["Pseudo"])
                self.grilleLabel[i][2].setText(str(l["Score"]))
                self.grilleLabel[i][3].setText(str(l["lignesCompletees"]))
                self.grilleLabel[i][4].setText(l["Date"])
                i+=1
            else:
                break
        if self.parent.master.pseudo!="":
            cur.execute("SELECT * FROM HighScores WHERE Pseudo =\'"+self.parent.master.pseudo+"\' ORDER BY Score DESC")
            lignes = cur.fetchall()
            i=1
            for l in lignes:
                if i < 11:
                    self.grilleLabel2[i][0].setText(str(i))
                    self.grilleLabel2[i][1].setText(l["Pseudo"])
                    self.grilleLabel2[i][2].setText(str(l["Score"]))
                    self.grilleLabel2[i][3].setText(str(l["lignesCompletees"]))
                    self.grilleLabel2[i][4].setText(l["Date"])
                    i+=1
                else:
                    break

        cur.close()
        conn.close()

class DialogLogin(QDialog): #petite fenêtre de login, je me suis amusé à employer plein de bidules, c'est pour ça qu'il y a autant de lignes de code
    def __init__(self, parent):
        self.parent = parent #on met un parent comme ça il n'est pas possible d'ignorer la fenêtre (elle reste au premier plan)
        super(DialogLogin, self).__init__()
        groupBox = QGroupBox("Etes-vous déjà inscrit?")
        self.radio1 = QRadioButton("S'inscrire")
        radio2 = QRadioButton("Se logger")
        radio2.setChecked(True)
        self.radio1.toggled.connect(self.signal) #lorsque un des radioButton change d'état, on envoie un signal pour cacher/révéler une partie du formulaire, de façon à s'adapter aux besoins de l'utilisateur
        layoutH = QHBoxLayout()
        layoutH.addWidget(self.radio1)
        layoutH.addWidget(radio2)
        groupBox.setLayout(layoutH)

        self.nom =  QLineEdit()
        self.prenom = QLineEdit()
        self.pseudo = QLineEdit()

        self.mdp =  QLineEdit()
        self.mdp.setEchoMode(QLineEdit.Password) #de cette manière les caractères entrés par l'utilisateur sont masqués

        self.confirm = QLineEdit()
        self.confirm.setEchoMode(QLineEdit.Password)

        self.infos = QLabel() #label servant à communiquer des messages d'erreurs à l'utilisateur
        self.infos.setStyleSheet("color:red")

        #formulaire d'inscription
        self.groupBoxInscription = QGroupBox("Inscription")
        formLayout = QFormLayout()
        formLayout.addRow("&Nom :", self.nom)
        formLayout.addRow("&Prénom :", self.prenom)
        formLayout.addRow("&Pseudo :", self.pseudo)
        formLayout.addRow("&Mot de passe :", self.mdp)
        formLayout.addRow("&Confirmez le mot de passe :", self.confirm)
        self.groupBoxInscription.setLayout(formLayout)
        self.groupBoxInscription.setVisible(False)

        #formulaire de login
        self.pseudo2 = QLineEdit()
        self.mdp2 =  QLineEdit()
        self.mdp2.setEchoMode(QLineEdit.Password)
        self.groupBoxLogin = QGroupBox("Login")
        formLayout2 = QFormLayout()
        formLayout2.addRow("&Pseudo : ", self.pseudo2)
        formLayout2.addRow("&Mot de passe : ", self.mdp2)
        self.groupBoxLogin.setLayout(formLayout2)
        self.groupBoxLogin.setVisible(True)

        layout = QVBoxLayout()
        layout.addWidget(groupBox)
        layout.addWidget(self.groupBoxInscription)
        layout.addWidget(self.groupBoxLogin)
        boutonValider = QPushButton("Valider")
        boutonValider.clicked.connect(self.valider)
        layout.addWidget(self.infos)
        layout.addWidget(boutonValider)
        self.setLayout(layout)
        self.setWindowTitle("Inscription/login")
        self.setWindowIcon(QIcon("Sprites/icone.png"))
        self.pseudo2.setFocus()

    def signal(self): #signal permettant de révéler/cacher une partie du formulaire, selon que l'utilisateur veut se connecter ou créer un compte
        if self.radio1.isChecked()==False:
            self.groupBoxInscription.setVisible(False)
            self.groupBoxLogin.setVisible(True)
        else:
            self.groupBoxInscription.setVisible(True)
            self.groupBoxLogin.setVisible(False)
    def valider(self): #fonction appelée lorsque l'on clique sur Valider
        if self.checkList()==True:
            if self.radio1.isChecked()==True:
                self.parent.board.labelInfos.setText("Bienvenue, "+self.pseudo.text()+" !\nHave fun and eat veggies!")
                self.parent.pseudo = self.pseudo.text()
            else:
                self.parent.board.labelInfos.setText("Bienvenue, "+self.pseudo2.text()+" !\nHave fun and eat veggies!")
                self.parent.pseudo = self.pseudo2.text()
            self.close()
    def checkList(self): #on vérifie que les champs sont remplis et que les mots de passe correspondent #à compléter avec du SQL
        conn = sqlite3.connect("BDDTetris.sq3")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        if self.radio1.isChecked()==True:
            if self.nom.text()!="" and self.prenom.text()!="" and self.mdp.text()!="" and self.confirm.text()!="" and self.pseudo.text()!="":
                if self.mdp.text()==self.confirm.text():
                    cur.execute("SELECT * FROM Joueur WHERE Pseudo=\'"+self.pseudo.text()+"\'")
                    l = cur.fetchone()
                    if l is None:
                        cur.execute("INSERT INTO Joueur(Nom, Prenom, Pseudo, MotDePasse) VALUES(?,?,?,?)", (self.nom.text(), self.prenom.text(), self.pseudo.text(), self.mdp.text()))
                        conn.commit()
                        cur.close()
                        conn.close
                        return True
                    else:
                        self.infos.setText("Pseudo déjà utilisé")
                    cur.close()
                    conn.close
                    return False
                self.infos.setText("Les mots de passe ne correspondent pas")
            self.infos.setText("Veuillez remplir les champs correctement")
            cur.close()
            conn.close
            return False
        else:
            if self.pseudo2.text()!="" and self.mdp2.text()!="":
                cur.execute("SELECT * FROM Joueur WHERE Pseudo=\'"+self.pseudo2.text()+"\'")
                ligne = cur.fetchone()
                if ligne is None:
                    self.infos.setText("Ce pseudo n'existe pas")
                    cur.close()
                    conn.close
                    return False
                if ligne["MotDePasse"]!=self.mdp2.text():
                    self.infos.setText("Mot de passe incorrect")
                    cur.close()
                    conn.close
                    return False
                cur.close()
                conn.close
                return True
            cur.close()
            conn.close
            return False
class DialogHelp(QDialog):#ya moyen de faire bcp plus classe, emploie un QGridLayout et 2 QLabel par ligne
    def __init__(self, parent):
        self.parent = parent
        super(DialogHelp, self).__init__()

        tabWidget = QTabWidget()
        bouton = QPushButton("Fermer")
        bouton.clicked.connect(self.close)
        layoutPrincipal = QVBoxLayout()

        regles = QWidget()
        touches = QWidget()

        labelRegles = QLabel("""Principe du Jeu :\n\nDes pièces de couleur et de formes différentes\n descendent du haut de l'écran.\n Le joueur ne peut pas ralentir ou empêcher cette chute mais\n peut l'accélérer ou décider à quel angle\n de rotation (0°, 90°, 180°, 270°) et\n à quel emplacement latéral l'objet peut atterrir.\n Lorsqu'une ligne horizontale est complétée sans vide,\n elle disparaît et les blocs supérieurs tombent.\n Si le joueur ne parvient pas à faire disparaître les lignes\n assez vite et que l'écran se remplit jusqu'en haut,\n il est submergé et la partie est finie.

                \n\n\nVladimir collectionne les petites licornes""")
        layoutRegles = QVBoxLayout()

        labelTouches = QLabel("Déplacement vers la droite:       D \nDéplacement vers la gauche:         A \nRotation de la pièce:       W \nAccélération de la pièce:      S \nPause:       P \nHard-drop:     Espace")
        layoutTouches= QVBoxLayout()

        layoutRegles.addWidget(labelRegles)
        layoutTouches.addWidget(labelTouches)

        regles.setLayout(layoutRegles)
        touches.setLayout(layoutTouches)
        tabWidget.addTab(regles, "Règles du jeu")
        tabWidget.addTab(touches, "Touches")

        layoutPrincipal.addWidget(tabWidget)
        layoutPrincipal.addWidget(bouton)
        self.setLayout(layoutPrincipal)

class Piece(object):
    def __init__(self, boss, ready=0): #Comme il n'y a que maxi 4 rotations par pi�ce, on gagne du temps � simplement les lister plut�t qu'� les calculer � chaque fois
        self.i,self.j = 3,0
        self.ready = ready
        self.etat=0 #etat de la rotation, de 0 � 3 : 0 = �tat normal, 1 = 90 degr�s anti-horaire, 2 = 180 degr�s anti-horaire...etc
        self.oldCoords = (self.i, self.j)
        self.oldEtat = 0
        self.index=0
        self.boss = boss
        self.baby = 1
        self.timeLastChange=time()
        self.currentCarre = ""
        self.carres=["Sprites/carre_piece/carre_jaune3.png","Sprites/carre_piece/carre_bleuc3.png","Sprites/carre_piece/carre_vert3.png","Sprites/carre_piece/carre_rouge3.png","Sprites/carre_piece/carre_orange3.png","Sprites/carre_piece/carre_bleuf3.png","Sprites/carre_piece/carre_violet3.png"]
        self.noms = ["O", "I","S", "Z", "L", "J", "T"]
        self.choisir()
        self.coords = self.getCoords(self.index, self.etat)
        if self.naPaLaPlace()==True:
            self.ready =0
            self.boss.master.gameOver()
        if self.ready ==1:
            self.create()
    def naPaLaPlace(self):
        for i in range(4):
            if self.boss.grille[self.coords[i][0]][self.coords[i][1]]!=0 and self.boss.grille[self.coords[i][0]][self.coords[i][1]]!=8:
                return True
    def getCoords(self, index, etat):
        i,j=self.i, self.j #copie pour all�ger le code
        pieces=[
                    [[[i,j],[i+1,j],[i,j+1],[i+1,j+1]],[[i,j],[i+1,j],[i,j+1],[i+1,j+1]],[[i,j],[i+1,j],[i,j+1],[i+1,j+1]],[[i,j],[i+1,j],[i,j+1],[i+1,j+1]]],    #O
                    [[[i,j+1],[i+1,j+1],[i+2,j+1],[i+3,j+1]],[[i+2,j],[i+2,j+1],[i+2,j+2],[i+2,j+3]],[[i,j+1],[i+1,j+1],[i+2,j+1],[i+3,j+1]],[[i+2,j],[i+2,j+1],[i+2,j+2],[i+2,j+3]]],    #I
                    [[[i,j+1],[i+1,j+1],[i+1,j],[i+2,j]],[[i+1,j+2],[i+1,j+1],[i,j+1],[i,j]],[[i,j+1],[i+1,j+1],[i+1,j],[i+2,j]],[[i+1,j+2],[i+1,j+1],[i,j+1],[i,j]]],    #S
                    [[[i,j],[i+1,j],[i+1,j+1],[i+2,j+1]],[[i,j+2],[i,j+1],[i+1,j+1],[i+1,j]],[[i,j],[i+1,j],[i+1,j+1],[i+2,j+1]],[[i,j+2],[i,j+1],[i+1,j+1],[i+1,j]]],    #Z
                    [[[i+2,j+1],[i+1,j+1],[i,j+1],[i,j+2]],[[i,j],[i+1,j],[i+1,j+1],[i+1,j+2]],[[i,j+1],[i+1,j+1],[i+2,j+1],[i+2,j]],[[i+1,j],[i+1,j+1],[i+1,j+2],[i+2,j+2]]],    #L
                    [[[i,j+1],[i+1,j+1],[i+2,j+1],[i+2,j+2]],[[i+1,j],[i+1,j+1],[i+1,j+2],[i,j+2]],[[i+2,j+1],[i+1,j+1],[i,j+1],[i,j]],[[i+1,j+2],[i+1,j+1],[i+1,j],[i+2,j]]],    #J
                    [[[i,j+1],[i+1,j+1],[i+2,j+1],[i+1,j+2]],[[i+1,j+2],[i+1,j+1],[i+1,j],[i,j+1]],[[i,j+1],[i+1,j+1],[i+2,j+1],[i+1,j]],[[i+1,j+2],[i+1,j+1],[i+1,j],[i+2,j+1]]]   #T
                    ]  #ce tableau contient les 4 pi�ces et leurs rotations respectives
        return pieces[index][etat]
    def create(self):
        for i in range(4):
            if self.baby==0:
                try:
                    self.boss.scene.removeItem(self.boss.imagesPiece[i])
                except TypeError:
                    pass
                else:
                    pass
            self.boss.grille[self.coords[i][0]][self.coords[i][1]]=8
            self.boss.imagesPiece[i]=self.boss.scene.addPixmap(QPixmap(self.currentCarre))
            self.boss.imagesPiece[i].setPos((self.coords[i][0]+1)*32,(self.coords[i][1]+1)*32)
    def sauvegarde(self):
        self.oldEtat = self.etat
        self.oldCoords = self.coords
    def cancel(self):
        self.etat = self.oldEtat
        self.coords = self.oldCoords
    def setPos(self,m_i, m_j):
        self.i+=m_i
        self.j+=m_j
    def move(self, newX=0, newY=0):
        self.baby = 0
        self.setLastChange()
        self.erase()
        self.setPos(newX, newY)
        self.coords = self.getCoords(self.index, self.etat)
        self.create()
    def tourne(self): #rotation de la piece en incrementant la variable de classe etat, sans oublier de mettre a jour self.currentPiece
        self.setLastChange()
        self.sauvegarde()
        self.erase()
        self.etat = (self.etat + 1)%4
        self.coords = self.getCoords(self.index,self.etat)
        if self.checkCollisions(0,0)==True:
                self.cancel()
        self.create()
    def erase(self):
        for i in range(4):
            self.boss.grille[self.coords[i][0]][self.coords[i][1]]=0
    def choisir(self): #choisit al�atoirement une pi�ce
        self.index=random.randint(0,6) #choisis al�atoirement un type de pi�ce
        self.currentCarre=self.carres[self.index] #texture actuelle
    def getMaxH(self):
        qmax = 0
        for i in range(4):
            if self.coords[i][0]>qmax:
                qmax = self.coords[i][0]
        return qmax
    def getMinH(self):
        qmin = 100
        for i in range(4):
            if self.coords[i][0]<qmin:
                qmin = self.coords[i][0]
        return qmin
    def getMaxV(self):
        qmax = 0
        for i in range(4):
            if self.coords[i][1]>qmax:
                qmax = self.coords[i][1]
        return qmax
    def checkCollisions(self, newX, newY):
        if self.getMaxH()+newX>self.boss.LARGEUR or self.getMinH()+newX<0 or self.getMaxV()+newY>self.boss.HAUTEUR:
            return True
        for i in range(4):
            if self.boss.grille[self.coords[i][0]+newX][self.coords[i][1]+newY]!=0: #pour qu'il n'y ait pas de collisions, faut que la grille soit vide (0), mais on accepte le code 8 sinon la pièce se collisionne avec elle-même.
                if self.boss.grille[self.coords[i][0]+newX][self.coords[i][1]+newY]!=8:
                    return True
        return False
    def setLastChange(self): #chaque fois que les coordonn�es de la pi�ce actuelle changent, cette fonction est appel�e. Elle perment de v�rifier si une pi�ce est pos�e
        self.timeLastChange = time()
    def estPosee(self): #la pi�ce est consid�r�e comme pos�e s'il n'y a pas de changement de coordonn�es en 0.2 seconde (� am�liorer selon les vrais crit�res)
        if self.boss.master.isPaused==True or self.boss.master.isGameOver==True:
            #self.boss.master.isOver = False
            return False
        if time()-self.timeLastChange >0.2:
            return True
        return False


if __name__ == "__main__":
    app=QApplication(sys.argv)
    tetris = Jeu()
    sys.exit(app.exec_())


