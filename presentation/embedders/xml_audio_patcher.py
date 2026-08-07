from pptx.oxml.ns import qn
from lxml import etree


class XmlAudioPatcher:

    # def patch(self, picture):

    #     print("Patching XML...")

    #     xml = picture._element

    #     print("Before:")
    #     print(etree.tostring(
    #         xml,
    #         pretty_print=True
    #     ).decode())

    def patch(self, picture):

        print("Patching XML...")

        xml = picture._element

        video = xml.find(".//" + qn("a:videoFile"))

        if video is None:

            print("videoFile not found")
            return

        print("Found videoFile!")

        audio = etree.Element(qn("a:audioFile"))

        for key, value in video.attrib.items():

            audio.set(key, value)

        parent = video.getparent()

        parent.replace(video, audio)

        # print("videoFile -> audioFile")

        # print("\n--- Relationships ---")

        part = picture.part

        # for rel_id, rel in part.rels.items():

        #     print("Id      :", rel_id)
        #     print("Type    :", rel.reltype)
        #     print("Target  :", rel.target_part.partname)
        #     print("----------------------------")


        # # inspection code 
        # for rel_id, rel in part.rels.items():

        #     if "video" in rel.reltype:

        #         print(type(rel))
        #         print(rel.__dict__)

        for rel_id, rel in part.rels.items():

            if "video" in rel.reltype:

                # print("Changing relationship...")

                rel._reltype = (
                    "http://schemas.openxmlformats.org/"
                    "officeDocument/2006/relationships/audio"
                )

                rel.reltype = (
                    "http://schemas.openxmlformats.org/"
                    "officeDocument/2006/relationships/audio"
                )

                # print(rel.reltype)