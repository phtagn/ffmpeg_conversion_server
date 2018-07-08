from helpers import helpers
import logging
import os
log = logging.getLogger(__name__)


class QtFastStart(object):
    supported_extensions = ['.mp4']
    name = 'qtfs'

    @classmethod
    def process(cls, inputfile):
        pathelements = helpers.breakdown(inputfile)
        temp_ext = '.QTFS'

        if not os.path.exists(inputfile):
            raise IOError(f'{inputfile} does not exist')

        if pathelements['extension'] in cls.supported_extensions:
            from qtfaststart import processor, exceptions

            log.info("Relocating MOOV atom to start of file.")

            outputfile = inputfile + temp_ext

            if os.path.exists(outputfile):
                os.remove(outputfile)

            try:
                processor.process(inputfile, outputfile)
            except exceptions.FastStartException:
                log.warning("QT FastStart did not run - perhaps moov atom was at the start already.")

            if outputfile:
                os.remove(inputfile)
                os.rename(outputfile, inputfile)


class PostProcessorFactory(object):
    supported_post_processors = [QtFastStart]

    @classmethod
    def get_post_processors(cls, post_processors: list):
        r = []
        for pp in post_processors:
            r.extend([p for p in cls.supported_post_processors if p.name == pp])

        return r



