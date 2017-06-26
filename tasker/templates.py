"""File which holds template definitions for shots and assets.

tasker.templates.py

Use this file to define new shot and or asset tasks, their dependencies and the order in which they appear in the UI.

"""
__author__ = 'Dominik'


#Tasks asstes
concept = 'concept'
modeling = 'modeling'
texturing = 'texturing'
rigging = 'rigging'
grooming = 'grooming'
tailoring = 'tailoring'
muscle = 'mucle'
asset_vfx = 'asset_vfx'

#Tasks shots
storyboard = 'storyboard'
mood = 'mood'
blockin = 'blockin'
animation = 'animation'
tech_check = 'tech_check'
shot_set = 'shot_set'
matte_painting = 'matte_painting'
mach_move= 'match_move'
cloth_sim = 'cloth_sim'
hair_sim = 'hair_sim'
muscle_sim = 'muscle_sim'
vfx = 'vfx'
camera_check = 'camera_check'
lighting = 'lighting'
rendering = 'rendering'
compositing = 'compositing'


asset = {'feature_animation_character_asset' : {'tasks': [concept, modeling, tailoring, texturing, grooming, rigging, muscle, asset_vfx],
                                        'dependencies' : {concept: [],
                                                          modeling: [concept, ],
                                                          texturing: [concept, modeling, tailoring, ],
                                                          rigging: [concept, modeling, ],
                                                          grooming: [concept, modeling, texturing, tailoring, ],
                                                          tailoring: [concept, modeling, ],
                                                          muscle: [modeling, rigging, ],
                                                          asset_vfx: [concept, modeling, rigging, ],
                                                          }
                                        },
         'feature_animation_prop_asset' : {'tasks' : [concept, modeling, texturing],
                                   'dependencies' : {concept: [],
                                                     modeling: [concept, ],
                                                     texturing: [concept, modeling, ],
                                                    }
                                   },
         'feature_animation_anim_prop_asset' : {'tasks' : [concept, modeling, texturing, rigging, ],
                                   'dependencies' : {concept: [],
                                                     modeling: [concept, ],
                                                     texturing: [concept, modeling, ],
                                                     rigging: [modeling, texturing, ],
                                                    }
                                   }
          }


shot = {'feature_animation_shot' : {'tasks' : [storyboard, mood, blockin, animation, tech_check, shot_set, matte_painting, cloth_sim, hair_sim, muscle_sim, vfx, camera_check, lighting, rendering, compositing],
                            'dependencies' : {storyboard: [],
                                              mood: [storyboard, ],
                                              blockin: [storyboard, ],
                                              animation: [blockin, ],
                                              tech_check: [animation, shot_set, ],
                                              shot_set: [animation, ],
                                              matte_painting: [animation, shot_set, tech_check],
                                              cloth_sim: [animation, muscle_sim],
                                              hair_sim: [animation, cloth_sim, muscle_sim, ],
                                              muscle_sim: [animation, tech_check, ],
                                              vfx: [animation, shot_set, ],
                                              camera_check: [animation, shot_set, cloth_sim, hair_sim, muscle_sim, vfx, ],
                                              lighting: [shot_set, cloth_sim, muscle_sim, vfx, camera_check, animation, ],
                                              rendering: [lighting, ],
                                              compositing: [rendering, ],
                                              }
                                    },
        'shortfilm_shot' : {'tasks': [storyboard, animation, lighting, rendering, compositing],
                            'dependencies' : {storyboard: [],
                                              animation: [storyboard],
                                              lighting: [animation],
                                              rendering: [lighting],
                                              compositing: [rendering]
                                              }
                            }
        }

templates_by_category = {'asset': asset,
                         'shot': shot,
                         }