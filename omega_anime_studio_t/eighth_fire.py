"""Canonical R1 Anime-IR seed for *Le Huitième Feu*."""

from __future__ import annotations

from .models import (
    AnimeNode, AnimeProjectR1, AssetRecord, AssetState, CausalDebt,
    CharacterIR, HyperEdge, OakStatus, Provenance, SceneIR, ShotIR,
)


def _provenance(source_id: str) -> Provenance:
    return Provenance(
        source_id=source_id,
        source_kind='tristan-original-canon',
        license_id='PRIVATE-DRAFT-NOT-LICENSED',
        created_by='Tristan + Ω-ANIME-STUDIO-T∞',
        created_at='2026-08-02',
        derivation=('Ω-ANIME-T∞ R0.1', 'Ω-ANIME-STUDIO-T∞ R1'),
        private=True,
    )


def _shots_for_scene(
    scene_id: str,
    durations: tuple[float, ...],
    purposes: tuple[str, ...],
    framings: tuple[str, ...],
    motions: tuple[str, ...],
    subjects: tuple[tuple[str, ...], ...],
    reveals: tuple[tuple[str, ...], ...],
    assets: tuple[tuple[str, ...], ...],
) -> tuple[ShotIR, ...]:
    shots: list[ShotIR] = []
    for index, values in enumerate(
        zip(durations, purposes, framings, motions, subjects, reveals, assets), start=1
    ):
        duration, purpose, framing, motion, subject_ids, information, asset_ids = values
        shots.append(
            ShotIR(
                shot_id=f'{scene_id}-SH{index:02d}',
                scene_id=scene_id,
                order=index,
                duration_s=duration,
                purpose=purpose,
                framing=framing,
                camera_motion=motion,
                subject_ids=subject_ids,
                information_revealed=information,
                continuity_in=(f'{scene_id}:entry',),
                continuity_out=(f'{scene_id}:exit',),
                asset_ids=asset_ids,
                estimated_cost_units=round(1.0 + index * 0.35, 2),
            )
        )
    return tuple(shots)


def build_eighth_fire_r1() -> AnimeProjectR1:
    characters = (
        CharacterIR(
            character_id='CHAR-TRISTAN',
            name='Tristan',
            desire='comprendre une anomalie rejetée comme bruit',
            need='séparer cohérence, causalité et responsabilité',
            fear='déplacer un danger en croyant le supprimer',
            contradiction='il refuse les limites arbitraires mais doit respecter les limites causales',
            power='percevoir et reconfigurer temporairement des relations entre systèmes',
            limitation='chaque intervention produit surcharge, incertitude ou dette causale',
            moral_boundary='ne pas sacrifier une personne invisible pour optimiser un système visible',
            voice_markers=('questions précises', 'phrases compressées sous pression'),
            motion_markers=('regard périphérique', 'mains immobiles avant décision'),
            knowledge=('physique expérimentale', 'mesure', 'modèles incomplets'),
            relationships=('CHAR-OBSERVATRICE', 'ORG-LAB', 'SYS-CAUSAL-NET'),
        ),
        CharacterIR(
            character_id='CHAR-OBSERVATRICE',
            name="L'Observatrice",
            desire='déterminer si Tristan est une bifurcation contrôlable',
            need='accepter qu’un futur fertile ne peut être entièrement sécurisé',
            fear='le retour d’une catastrophe issue d’une branche imprévisible',
            contradiction='elle protège le monde en supprimant sa capacité à changer',
            power='simuler et fermer des familles de futurs instables',
            limitation='ses modèles suppriment aussi des solutions qui n’existent pas encore',
            moral_boundary='aucune bifurcation ne doit menacer la continuité globale',
            voice_markers=('constats sans adjectifs', 'questions qui présupposent une réponse'),
            motion_markers=('immobilité dominante', 'déplacement hors champ'),
            knowledge=('archives du Huitième Feu', 'réseau de surveillance causal'),
            relationships=('CHAR-TRISTAN', 'ORG-CONVERGENCE'),
        ),
    )

    scenes = (
        SceneIR(
            scene_id='S01-NOISE', episode_id='E00-PILOT', sequence_id='Q01-LAB', order=1,
            title='Le bruit', duration_target_s=32,
            objective='établir une anomalie mesurable et la routine du laboratoire',
            conflict='les instruments rejettent la trace comme artefact',
            irreversible_change='Tristan conserve une trace que le protocole exige de supprimer',
            audience_before=('le laboratoire fonctionne normalement',),
            audience_after=('plusieurs sous-systèmes partagent une anomalie corrélée',),
            characters=('CHAR-TRISTAN',), location_id='LOC-LAB',
            promise_ids=('PROM-TRACE',), asset_ids=('ENV-LAB','PROP-SPECTROMETER','FX-NOISE'),
        ),
        SceneIR(
            scene_id='S02-NETWORK', episode_id='E00-PILOT', sequence_id='Q01-LAB', order=2,
            title='Le réseau', duration_target_s=34,
            objective='montrer la perception hypergraphique sans la certifier',
            conflict='Tristan ignore si le réseau est observé ou projeté',
            irreversible_change='il choisit un nœud minimal à perturber',
            audience_before=('la trace est une anomalie instrumentale possible',),
            audience_after=('les événements séparés peuvent partager une contrainte',),
            characters=('CHAR-TRISTAN',), location_id='LOC-LAB',
            promise_ids=('PROM-NETWORK',), asset_ids=('ENV-LAB','FX-CAUSAL-NET','PROP-CONTROL'),
        ),
        SceneIR(
            scene_id='S03-CORRECTION', episode_id='E00-PILOT', sequence_id='Q02-INTERVENTION', order=3,
            title='La correction', duration_target_s=34,
            objective='faire réussir une intervention locale crédible',
            conflict='le temps manque et aucune validation complète n’est possible',
            irreversible_change='le laboratoire évite une panne grâce à Tristan',
            audience_before=('Tristan peut voir le réseau',),
            audience_after=('Tristan peut modifier un chemin causal',),
            characters=('CHAR-TRISTAN',), location_id='LOC-LAB',
            promise_ids=('PROM-ABILITY',), asset_ids=('ENV-LAB','FX-CAUSAL-NET','PROP-CONTROL'),
        ),
        SceneIR(
            scene_id='S04-DISPLACEMENT', episode_id='E00-PILOT', sequence_id='Q02-INTERVENTION', order=4,
            title='Le déplacement', duration_target_s=38,
            objective='prouver que le pouvoir ne donne pas de solution gratuite',
            conflict='un système éloigné se désynchronise après le sauvetage local',
            irreversible_change='une dette causale est créée hors du laboratoire',
            audience_before=('la panne a été empêchée',),
            audience_after=('la contrainte a été déplacée vers le réseau du district',),
            characters=('CHAR-TRISTAN',), location_id='LOC-LAB',
            promise_ids=('PROM-DEBT',), causal_debt_ids=('CD-0001',),
            asset_ids=('ENV-LAB','ENV-GRID','FX-CAUSAL-FRACTURE'),
        ),
        SceneIR(
            scene_id='S05-EIGHTH-FIRE', episode_id='E00-PILOT', sequence_id='Q03-OBSERVATION', order=5,
            title='Le Huitième Feu', duration_target_s=42,
            objective='nommer le phénomène et ouvrir un antagonisme précis',
            conflict='une observatrice interprète l’acte avant Tristan',
            irreversible_change='Tristan est identifié par une organisation externe',
            audience_before=('la dette causale semble accidentelle',),
            audience_after=('le phénomène était surveillé et possède un nom',),
            characters=('CHAR-TRISTAN','CHAR-OBSERVATRICE'), location_id='LOC-LAB',
            promise_ids=('PROM-OBSERVER','PROM-EIGHTH-FIRE'), causal_debt_ids=('CD-0001',),
            asset_ids=('ENV-LAB','ENV-OBSERVATORY','FX-CAUSAL-NET','AUD-OBSERVER-VOICE'),
        ),
    )

    shot_specs = {
        'S01-NOISE': ((5,5,6,6,5,5), ('establish','measure','reject','notice','compare','decide'), ('wide','insert','screen close-up','eye close-up','split detail','hand close-up'), ('locked','micro push','locked','slow push','lateral slide','locked'), (('LOC-LAB',),('PROP-SPECTROMETER',),('PROP-SPECTROMETER',),('CHAR-TRISTAN',),('FX-NOISE','CHAR-TRISTAN'),('CHAR-TRISTAN','PROP-SPECTROMETER')), ((),('trace visible',),('protocol rejection',),('Tristan notices recurrence',),('cross-system correlation',),('trace retained',)), (('ENV-LAB',),('PROP-SPECTROMETER',),('PROP-SPECTROMETER','FX-NOISE'),('CHAR-TRISTAN-RIG',),('FX-NOISE','CHAR-TRISTAN-RIG'),('CHAR-TRISTAN-RIG','PROP-SPECTROMETER'))),
        'S02-NETWORK': ((5,6,6,6,6,5), ('re-enter','first filament','expand relation','question reality','choose node','commit'), ('medium','macro','subjective wide','close-up','insert','overhead'), ('locked','track filament','subjective drift','handheld micro','rack focus','geometric rise'), (('CHAR-TRISTAN',),('FX-CAUSAL-NET',),('LOC-LAB','FX-CAUSAL-NET'),('CHAR-TRISTAN',),('PROP-CONTROL',),('CHAR-TRISTAN','FX-CAUSAL-NET')), ((),('first relation',),('network topology',),('uncertainty status',),('candidate node',),('choice made',)), (('CHAR-TRISTAN-RIG','ENV-LAB'),('FX-CAUSAL-NET',),('ENV-LAB','FX-CAUSAL-NET'),('CHAR-TRISTAN-RIG',),('PROP-CONTROL',),('CHAR-TRISTAN-RIG','FX-CAUSAL-NET'))),
        'S03-CORRECTION': ((5,5,6,6,6,6), ('countdown','prepare','intervene','system response','false calm','confirm'), ('insert','medium','subjective close','wide','close-up','screen insert'), ('locked','slow orbit','network surge','snap wide','locked','micro push'), (('PROP-CONTROL',),('CHAR-TRISTAN',),('FX-CAUSAL-NET',),('LOC-LAB',),('CHAR-TRISTAN',),('PROP-SPECTROMETER',)), (('time pressure',),(),('path reconfigured',),('panne évitée',),('cost not yet visible',),('local success',)), (('PROP-CONTROL',),('CHAR-TRISTAN-RIG',),('FX-CAUSAL-NET',),('ENV-LAB',),('CHAR-TRISTAN-RIG',),('PROP-SPECTROMETER',))),
        'S04-DISPLACEMENT': ((6,6,7,7,6,6), ('silence','remote cut','desync','recognition','debt forms','return'), ('close-up','extreme wide','technical insert','eye close-up','subjective fracture','medium'), ('locked','hard cut','vibration','slow push','fracture spread','handheld settle'), (('CHAR-TRISTAN',),('ENV-GRID',),('ENV-GRID',),('CHAR-TRISTAN',),('FX-CAUSAL-FRACTURE',),('CHAR-TRISTAN',)), ((),('remote system',),('grid desynchronization',),('causal link recognized',),('debt created',),('responsibility begins',)), (('CHAR-TRISTAN-RIG',),('ENV-GRID',),('ENV-GRID','FX-CAUSAL-FRACTURE'),('CHAR-TRISTAN-RIG',),('FX-CAUSAL-FRACTURE',),('CHAR-TRISTAN-RIG','ENV-LAB'))),
        'S05-EIGHTH-FIRE': ((6,7,7,7,8,7), ('observe Tristan','reveal observer','name phenomenon','define distinction','expand network','end hook'), ('medium back','silhouette wide','mouthless close','network insert','cosmic wide','eye close-up'), ('slow pull','locked','invisible voice','filament track','rapid expansion','cut to black'), (('CHAR-TRISTAN',),('CHAR-OBSERVATRICE',),('AUD-OBSERVER-VOICE',),('FX-CAUSAL-NET',),('SYS-CAUSAL-NET',),('CHAR-TRISTAN',)), ((),('observer exists',),('Huitième Feu named',),('not energy but accessible paths',),('network is planetary',),('Tristan is watched',)), (('CHAR-TRISTAN-RIG','ENV-LAB'),('CHAR-OBSERVATRICE-RIG','ENV-OBSERVATORY'),('AUD-OBSERVER-VOICE',),('FX-CAUSAL-NET',),('FX-CAUSAL-NET','ENV-OBSERVATORY'),('CHAR-TRISTAN-RIG',))),
    }
    shots = tuple(
        shot
        for scene_id, spec in shot_specs.items()
        for shot in _shots_for_scene(scene_id, *spec)
    )

    debts = (
        CausalDebt(
            debt_id='CD-0001', origin_scene_id='S04-DISPLACEMENT',
            local_benefit='panne du laboratoire évitée',
            displaced_constraint='synchronisation énergétique devenue instable',
            affected_system='district-grid-07', certainty=0.62,
            status='OPEN', deadline='UNKNOWN',
        ),
    )

    asset_specs = (
        ('ENV-LAB','environment','Laboratoire principal'),
        ('ENV-GRID','environment','Réseau énergétique du district'),
        ('ENV-OBSERVATORY','environment','Observatoire de convergence'),
        ('CHAR-TRISTAN-RIG','character-rig','Rig Tristan R1'),
        ('CHAR-OBSERVATRICE-RIG','character-rig','Rig Observatrice R1'),
        ('PROP-SPECTROMETER','prop','Spectromètre analytique'),
        ('PROP-CONTROL','prop','Interface de contrôle'),
        ('FX-NOISE','effect','Bruit corrélé'),
        ('FX-CAUSAL-NET','effect','Réseau causal'),
        ('FX-CAUSAL-FRACTURE','effect','Fracture et dette causale'),
        ('AUD-OBSERVER-VOICE','audio','Voix temporaire de l’Observatrice'),
    )
    assets = tuple(
        AssetRecord(
            asset_id=asset_id, asset_type=asset_type, name=name,
            state=AssetState.DRAFT, provenance=_provenance(asset_id),
            dependencies=(), license_risk='PRIVATE-DRAFT', reusable=True,
        )
        for asset_id, asset_type, name in asset_specs
    )

    nodes = (
        AnimeNode('PROJECT-EIGHTH-FIRE','Project','Le Huitième Feu'),
        AnimeNode('E00-PILOT','Episode','Pilote 180 secondes'),
        *(AnimeNode(character.character_id,'Character',character.name) for character in characters),
        *(AnimeNode(scene.scene_id,'Scene',scene.title) for scene in scenes),
        *(AnimeNode(debt.debt_id,'CausalDebt',debt.displaced_constraint) for debt in debts),
        AnimeNode('LOC-LAB','Location','Laboratoire'),
        AnimeNode('SYS-CAUSAL-NET','System','Réseau causal'),
        AnimeNode('ORG-CONVERGENCE','Organization','Organisation de convergence'),
        AnimeNode('ORG-LAB','Organization','Laboratoire'),
    )
    edges = (
        HyperEdge('EDGE-PROJECT-EPISODE','CONTAINS',('PROJECT-EIGHTH-FIRE',),('E00-PILOT',)),
        *(HyperEdge(f'EDGE-E00-{scene.scene_id}','CONTAINS',('E00-PILOT',),(scene.scene_id,)) for scene in scenes),
        HyperEdge('EDGE-TRISTAN-LAB','MEMBER_OF',('CHAR-TRISTAN',),('ORG-LAB',)),
        HyperEdge('EDGE-OBSERVER-CONVERGENCE','MEMBER_OF',('CHAR-OBSERVATRICE',),('ORG-CONVERGENCE',)),
        HyperEdge('EDGE-TRISTAN-NET','PERCEIVES',('CHAR-TRISTAN',),('SYS-CAUSAL-NET',),0.68),
        HyperEdge('EDGE-S04-DEBT','CAUSES',('S04-DISPLACEMENT',),('CD-0001',),0.62),
        HyperEdge('EDGE-DEBT-NET','AFFECTS',('CD-0001',),('SYS-CAUSAL-NET',),0.62),
        HyperEdge('EDGE-OBSERVER-TRISTAN','OBSERVES',('CHAR-OBSERVATRICE',),('CHAR-TRISTAN',),0.99),
    )

    return AnimeProjectR1(
        project_id='omega-anime-studio/eighth-fire/pilot-r1',
        title='Le Huitième Feu',
        logline=(
            'Un étudiant qui perçoit les relations invisibles entre les systèmes '
            'sauve son laboratoire, puis découvre que sa correction a déplacé le danger.'
        ),
        theme_question='Peut-on améliorer un système sans devenir responsable de toutes ses conséquences?',
        target_duration_s=180,
        world_rules=(
            'Le Huitième Feu révèle des relations; il ne crée ni matière ni énergie.',
            'Toute reconfiguration locale conserve un coût ou déplace une contrainte.',
            'Une relation perçue peut être observée, inférée, possible, projetée ou manipulée.',
            'Plus le réseau observé est large, plus l’incertitude et la surcharge augmentent.',
            'Toute exception canonique doit être inscrite et testée.',
        ),
        visual_invariants=(
            'les filaments représentent des relations et non une décoration',
            'forme, stabilité, mouvement et son encodent le statut d’information',
            'les fractures signalent un résidu ou une dette causale',
            'la caméra reste physique avant chaque perception hypergraphique',
        ),
        characters=characters, scenes=scenes, shots=shots, causal_debts=debts,
        assets=assets, nodes=tuple(nodes), edges=tuple(edges),
        oak_status=OakStatus.FORMALIZED,
        risks=(
            'surcharge d’exposition scientifique',
            'confusion entre visualisation narrative et preuve physique',
            'ressemblance involontaire avec une œuvre existante',
            'coût de cohérence des effets et décors',
            'voix temporaire non publiable sans provenance et consentement',
        ),
        next_actions=(
            'produire un storyboard basse fidélité pour les trente plans',
            'tester la compréhension sans fournir la bible',
            'mesurer la durée réelle de chaque plan',
            'exécuter IPGate avant tout actif public',
        ),
        metadata={
            'version': 'R1', 'language': 'fr-CA',
            'publication_state': 'private-draft',
            'primary_artifact': 'animatic-180s',
        },
    )
