# Visual Spec

## Source
- Reference image: smoke-test.png
- Target drawio: smoke-test.drawio
- Canvas: 800 x 600
- Font policy: use source font when specified

## Global Style
- Background: white
- Primary font: Arial
- Stroke style: rounded rectangles
- Arrow style: classic arrows
- Color palette: gray, blue

## Regions
| id | bbox x,y,w,h | role | visual notes |
| main | 40,40,720,520 | sample | one central region |

## Text Blocks
| id | bbox x,y,w,h | text | font | alignment | priority |
| title | 60,60,200,40 | Smoke | Arial | left | high |

## Shapes
| id | bbox x,y,w,h | type | fill | stroke | notes |
| box | 100,100,200,80 | rounded | #ffffff | #666666 | sample |

## Connectors
| id | from | to | route | arrowheads | label | notes |
| e1 | a | b | straight | end | | sample |

## Icons And Images
| id | bbox x,y,w,h | meaning | exact/approx/missing | replacement plan |
| icon1 | 0,0,0,0 | none | missing | not needed |
